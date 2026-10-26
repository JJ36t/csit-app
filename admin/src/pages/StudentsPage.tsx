import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Divider,
  Input,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd';
import {
  DownloadOutlined,
  InboxOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import {
  ApiError,
  downloadTemplate,
  importStudents,
  listDepartments,
  listStudents,
  type Department,
  type ImportIssue,
  type ImportResult,
  type StudentRow,
} from '../api';

const { Paragraph, Text } = Typography;

const studyLabel: Record<string, string> = { morning: 'صباحي', evening: 'مسائي' };

const errorColumns = [
  { title: 'الصف', dataIndex: 'row', width: 70 },
  { title: 'العمود', dataIndex: 'column', width: 140 },
  { title: 'الرمز', dataIndex: 'code', width: 180, render: (code: string) => <Tag>{code}</Tag> },
  { title: 'الرسالة', dataIndex: 'message_ar' },
];

const studentColumns = [
  { title: 'الرقم الجامعي', dataIndex: 'university_id', width: 130 },
  { title: 'الاسم', dataIndex: 'full_name_ar' },
  {
    title: 'القسم',
    dataIndex: 'department_name_ar',
    width: 150,
    render: (name: string, row: StudentRow) => `${name} (${row.department_code})`,
  },
  { title: 'المرحلة', dataIndex: 'stage', width: 80 },
  {
    title: 'الدراسة',
    dataIndex: 'study_type',
    width: 90,
    render: (value: string) => studyLabel[value] ?? value,
  },
  {
    title: 'الشعبة',
    dataIndex: 'group_name',
    width: 90,
    render: (value: string | null) => value ?? '—',
  },
];

export default function StudentsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  const [rows, setRows] = useState<StudentRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState('');
  const [department, setDepartment] = useState<string | undefined>();
  const [stage, setStage] = useState<number | undefined>();
  const [study, setStudy] = useState<string | undefined>();
  const [departments, setDepartments] = useState<Department[]>([]);

  useEffect(() => {
    listDepartments()
      .then(setDepartments)
      .catch(() => message.error('تعذّر تحميل قائمة الأقسام'));
  }, []);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const res = await listStudents({
        q,
        department_code: department,
        stage,
        study_type: study,
        page,
        limit: 20,
      });
      setRows(res.items);
      setTotal(res.total);
    } catch (e) {
      message.error(e instanceof ApiError ? e.message : 'تعذّر تحميل قائمة الطلاب');
    } finally {
      setLoading(false);
    }
  }, [q, department, stage, study, page]);

  useEffect(() => {
    void load();
  }, [load]);

  const run = async (dryRun: boolean): Promise<void> => {
    if (!file) {
      message.warning('اختر ملف Excel أولاً');
      return;
    }
    setRunning(true);
    try {
      const res = await importStudents(file, dryRun);
      setResult(res);
      if (dryRun) {
        message.info('انتهى الفحص؛ لم يُنشأ أي حساب');
      } else {
        message.success(`أُنشئ ${res.created_count} حساباً`);
        setPage(1);
        await load();
      }
    } catch (e) {
      message.error(e instanceof ApiError ? e.message : 'تعذّر تنفيذ الاستيراد');
    } finally {
      setRunning(false);
    }
  };

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card
        title="استيراد الطلاب من Excel"
        extra={
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {
              downloadTemplate().catch(() => message.error('تعذّر تنزيل القالب'));
            }}
          >
            تنزيل القالب
          </Button>
        }
      >
        <Paragraph type="secondary" style={{ marginTop: 0 }}>
          الأعمدة المطلوبة: <Text code>university_id</Text> · <Text code>full_name_ar</Text> ·{' '}
          <Text code>department_code</Text> · <Text code>stage</Text> ·{' '}
          <Text code>study_type</Text> — والاختيارية: <Text code>group_name</Text> ·{' '}
          <Text code>enrollment_year</Text> · <Text code>email</Text> · <Text code>phone</Text>.
          الشُعب تُنشأ تلقائياً عند غيابها، وكلمة المرور الأولية لكل طالب هي رقمه الجامعي مع إجبار
          التغيير عند أول دخول.
        </Paragraph>

        <Upload.Dragger
          accept=".xlsx"
          maxCount={1}
          fileList={fileList}
          beforeUpload={(selected) => {
            setFile(selected as File);
            setFileList([{ uid: selected.name, name: selected.name }]);
            setResult(null);
            return false; // لا رفع تلقائي — النقر على الأزرار ينفّذ
          }}
          onRemove={() => {
            setFile(null);
            setFileList([]);
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">اسحب ملف Excel (xlsx) هنا أو اضغط للاختيار</p>
          <p className="ant-upload-hint">الحد الأقصى 5 ميغابايت</p>
        </Upload.Dragger>

        <Space style={{ marginTop: 16 }}>
          <Button
            icon={<SafetyCertificateOutlined />}
            onClick={() => void run(true)}
            loading={running}
          >
            فحص فقط (دون إنشاء)
          </Button>
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={() => void run(false)}
            loading={running}
          >
            تنفيذ الاستيراد
          </Button>
        </Space>

        {result && (
          <Card size="small" style={{ marginTop: 16 }} title={result.dry_run ? 'نتيجة الفحص' : 'نتيجة الاستيراد'}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic title="الصفوف" value={result.rows_total} />
              </Col>
              <Col span={6}>
                <Statistic title="صالحة" value={result.rows_valid} valueStyle={{ color: '#237804' }} />
              </Col>
              <Col span={6}>
                <Statistic title="خاطئة" value={result.rows_invalid} valueStyle={{ color: '#a8071a' }} />
              </Col>
              <Col span={6}>
                <Statistic title="حسابات أُنشئت" value={result.created_count} />
              </Col>
            </Row>

            {result.groups_created.length > 0 && (
              <Alert
                style={{ marginTop: 12 }}
                type="info"
                showIcon
                message={`شُعب أُنشئت تلقائياً (${result.groups_created.length}): ${result.groups_created.join(' · ')}`}
              />
            )}

            {result.errors.length > 0 && (
              <>
                <Divider orientation="right">
                  تقرير الأخطاء ({result.errors.length}
                  {result.errors_truncated ? ' — مختصر' : ''})
                </Divider>
                <Table<ImportIssue>
                  size="small"
                  rowKey={(row) => `${row.row}-${row.column}-${row.code}`}
                  dataSource={result.errors}
                  columns={errorColumns}
                  pagination={{ pageSize: 8, hideOnSinglePage: true }}
                />
              </>
            )}

            {result.errors.length === 0 && (
              <Alert style={{ marginTop: 12 }} type="success" showIcon message="لا أخطاء — كل الصفوف سليمة" />
            )}
          </Card>
        )}
      </Card>

      <Card title="الطلاب المسجّلون">
        <Space wrap style={{ marginBottom: 12 }}>
          <Input.Search
            allowClear
            placeholder="ابحث بالاسم أو الرقم الجامعي"
            style={{ width: 260 }}
            onSearch={(value) => {
              setPage(1);
              setQ(value);
            }}
          />
          <Select
            allowClear
            placeholder="القسم"
            style={{ width: 170 }}
            value={department}
            onChange={(value) => {
              setPage(1);
              setDepartment(value);
            }}
            options={departments.map((item) => ({
              value: item.code,
              label: item.name_ar,
            }))}
          />
          <Select
            allowClear
            placeholder="المرحلة"
            style={{ width: 120 }}
            value={stage}
            onChange={(value) => {
              setPage(1);
              setStage(value);
            }}
            options={[1, 2, 3, 4, 5, 6].map((value) => ({ value, label: `المرحلة ${value}` }))}
          />
          <Select
            allowClear
            placeholder="الدراسة"
            style={{ width: 130 }}
            value={study}
            onChange={(value) => {
              setPage(1);
              setStudy(value);
            }}
            options={[
              { value: 'morning', label: 'صباحي' },
              { value: 'evening', label: 'مسائي' },
            ]}
          />
        </Space>

        <Table<StudentRow>
          size="middle"
          rowKey="university_id"
          loading={loading}
          dataSource={rows}
          columns={studentColumns}
          pagination={{
            current: page,
            pageSize: 20,
            total,
            showSizeChanger: false,
            onChange: (nextPage) => setPage(nextPage),
          }}
          locale={{ emptyText: 'لا يوجد طلاب بعد — استورد ملف Excel أعلاه' }}
        />
      </Card>
    </Space>
  );
}
