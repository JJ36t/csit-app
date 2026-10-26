import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Divider,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import {
  CloudUploadOutlined,
  DeleteOutlined,
  DownloadOutlined,
  LockOutlined,
  PlusOutlined,
  ReloadOutlined,
  SaveOutlined,
} from '@ant-design/icons';
import {
  ApiError,
  createAssessment,
  deleteAssessment,
  downloadGrades,
  getOfferingGrades,
  listOfferings,
  publishAssessment,
  saveGrades,
  type Assessment,
  type Offering,
  type OfferingGrades,
  type StudentGradeRow,
} from '../api';

const { Text, Paragraph } = Typography;

const assessmentKindLabel: Record<string, string> = {
  quiz: 'كويز',
  lab: 'مختبر',
  midterm: 'امتحان نصفي',
  final: 'امتحان نهائي',
  other: 'أخرى',
};

const studyLabel: Record<string, string> = { morning: 'صباحي', evening: 'مسائي' };

interface AssessmentFormValues {
  name: string;
  kind: string;
  max_score: number;
  weight: number;
}

interface Notice {
  kind: 'success' | 'error' | 'info' | 'warning';
  text: string;
  hint?: string;
}

function failureText(error: unknown, fallback: string): Notice {
  if (error instanceof ApiError) {
    return {
      kind: 'error',
      text: error.message,
      hint: `${error.code}${error.details ? ` · ${JSON.stringify(error.details)}` : ''}`,
    };
  }
  return { kind: 'error', text: fallback };
}

export default function GradesPage({ canPublish }: { canPublish: boolean }) {
  const [offerings, setOfferings] = useState<Offering[]>([]);
  const [offeringId, setOfferingId] = useState<string | undefined>();
  const [data, setData] = useState<OfferingGrades | null>(null);
  const [edits, setEdits] = useState<Record<string, Record<string, number | null>>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [form] = Form.useForm<AssessmentFormValues>();
  const requestId = useRef(0);

  useEffect(() => {
    listOfferings()
      .then((res) => {
        setOfferings(res.items);
        if (res.items.length > 0) setOfferingId((current) => current ?? res.items[0].offering_id);
      })
      .catch(() => message.error('تعذّر تحميل قائمة المواد'));
  }, []);

  const selected = offerings.find((item) => item.offering_id === offeringId);

  const load = useCallback(async (id: string): Promise<void> => {
    const ticket = requestId.current + 1;
    requestId.current = ticket;
    setLoading(true);
    try {
      const res = await getOfferingGrades(id);
      if (ticket !== requestId.current) return; // ردّ قديم لمادة أخرى
      setData(res);
      setEdits({});
    } catch (error) {
      if (ticket !== requestId.current) return;
      setData(null);
      setNotice(failureText(error, 'تعذّر تحميل درجات المادة'));
    } finally {
      if (ticket === requestId.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    setNotice(null);
    if (offeringId) void load(offeringId);
    else setData(null);
  }, [offeringId, load]);

  const weightUsed = useMemo(
    () =>
      (data?.assessments ?? []).reduce((total, item) => total + Number(item.weight ?? 0), 0),
    [data],
  );

  const cellValue = (assessmentId: string, student: StudentGradeRow): number | null => {
    const assessmentEdits = edits[assessmentId];
    if (assessmentEdits && Object.prototype.hasOwnProperty.call(assessmentEdits, student.student_id)) {
      return assessmentEdits[student.student_id];
    }
    return student.scores[assessmentId] ?? null;
  };

  const setCell = (assessmentId: string, studentId: string, value: number | null): void => {
    setEdits((current) => {
      const assessmentEdits = { ...(current[assessmentId] ?? {}) };
      if (value === null) delete assessmentEdits[studentId];
      else assessmentEdits[studentId] = value;

      const merged = { ...current };
      if (Object.keys(assessmentEdits).length === 0) delete merged[assessmentId];
      else merged[assessmentId] = assessmentEdits;
      return merged;
    });
  };

  const pendingRows = (assessment: Assessment): { student_id: string; score: number }[] => {
    const rows: { student_id: string; score: number }[] = [];
    const assessmentEdits = edits[assessment.assessment_id] ?? {};
    (data?.students ?? []).forEach((student) => {
      if (!Object.prototype.hasOwnProperty.call(assessmentEdits, student.student_id)) return;
      const value = assessmentEdits[student.student_id];
      if (value === null || value === undefined) return;
      if (value === student.scores[assessment.assessment_id]) return;
      rows.push({ student_id: student.student_id, score: value });
    });
    return rows;
  };

  const dirtyAssessmentIds = (data?.assessments ?? [])
    .filter((item) => !item.is_published && pendingRows(item).length > 0)
    .map((item) => item.assessment_id);

  /** تأكيد قبل أي إعادة تحميل تُسقط تعديلات غير محفوظة. */
  const canDiscard = (action: string): Promise<boolean> => {
    if (dirtyAssessmentIds.length === 0) return Promise.resolve(true);
    return new Promise((resolve) => {
      Modal.confirm({
        title: 'توجد تعديلات غير محفوظة',
        content: `${action} سيتجاهل التعديلات في ${dirtyAssessmentIds.length} تقييم دون حفظها.`,
        okText: 'متابعة',
        cancelText: 'إلغاء',
        onOk: () => resolve(true),
        onCancel: () => resolve(false),
      });
    });
  };

  const save = async (): Promise<void> => {
    if (!data) return;
    if (dirtyAssessmentIds.length === 0) {
      message.info('لا تعديلات لحفظها');
      return;
    }
    setSaving(true);
    setNotice(null);
    try {
      let created = 0;
      let updated = 0;
      for (const assessment of data.assessments) {
        if (!dirtyAssessmentIds.includes(assessment.assessment_id)) continue;
        const rows = pendingRows(assessment);
        const result = await saveGrades(assessment.assessment_id, rows);
        created += result.created;
        updated += result.updated;
      }
      setNotice({
        kind: 'success',
        text: `حُفظت الدرجات: ${created} جديدة و${updated} معدّلة (كمسودة — لا يراها الطالب قبل النشر)`,
      });
      await load(data.offering_id);
    } catch (error) {
      setNotice(failureText(error, 'تعذّر حفظ الدرجات'));
    } finally {
      setSaving(false);
    }
  };

  const publish = async (assessment: Assessment): Promise<void> => {
    if (!data) return;
    if (!(await canDiscard('نشر التقييم'))) return;
    setPublishing(true);
    setNotice(null);
    try {
      const result = await publishAssessment(assessment.assessment_id);
      setNotice({
        kind: 'success',
        text: `نُشر «${assessment.name}» وأُشعر ${result.notified} طالباً`,
      });
      await load(data.offering_id);
    } catch (error) {
      setNotice(failureText(error, 'تعذّر نشر التقييم'));
    } finally {
      setPublishing(false);
    }
  };

  const remove = async (assessment: Assessment): Promise<void> => {
    if (!data) return;
    if (!(await canDiscard('حذف التقييم'))) return;
    setNotice(null);
    try {
      await deleteAssessment(assessment.assessment_id);
      setNotice({ kind: 'success', text: `حُذف التقييم «${assessment.name}»` });
      await load(data.offering_id);
    } catch (error) {
      setNotice(failureText(error, 'تعذّر حذف التقييم'));
    }
  };

  const create = async (values: AssessmentFormValues): Promise<void> => {
    if (!offeringId) return;
    if (!(await canDiscard('إنشاء تقييم جديد'))) return;
    setSaving(true);
    setNotice(null);
    try {
      const created = await createAssessment({
        offering_id: offeringId,
        name: values.name.trim(),
        kind: values.kind,
        max_score: values.max_score,
        weight: values.weight,
      });
      setNotice({
        kind: 'success',
        text: `أُنشئ التقييم «${created.name}» (/${created.max_score} ×${created.weight})`,
      });
      form.resetFields(['name', 'max_score', 'weight']);
      await load(offeringId);
    } catch (error) {
      setNotice(failureText(error, 'تعذّر إنشاء التقييم'));
    } finally {
      setSaving(false);
    }
  };

  const exportFile = async (): Promise<void> => {
    if (!selected) return;
    try {
      await downloadGrades(selected.offering_id, selected.course_code);
    } catch (error) {
      setNotice(failureText(error, 'تعذّر تصدير الدرجات'));
    }
  };

  const assessmentColumns = [
    { title: 'التقييم', dataIndex: 'name' },
    {
      title: 'النوع',
      dataIndex: 'kind',
      width: 120,
      render: (value: string) => assessmentKindLabel[value] ?? value,
    },
    { title: 'العظمى', dataIndex: 'max_score', width: 90 },
    { title: 'الوزن', dataIndex: 'weight', width: 90 },
    {
      title: 'الحالة',
      dataIndex: 'is_published',
      width: 130,
      render: (value: boolean) =>
        value ? <Tag color="green">منشور</Tag> : <Tag color="gold">مسودة</Tag>,
    },
    {
      title: 'إجراءات',
      key: 'actions',
      width: 230,
      render: (_: unknown, row: Assessment) => (
        <Space size={4}>
          <Popconfirm
            title={`نشر «${row.name}»؟`}
            description="بعد النشر لا يمكن تعديل الدرجات، ويُشعَر الطلاب المسجَّلون."
            okText="نشر"
            cancelText="إلغاء"
            disabled={row.is_published || !canPublish}
            onConfirm={() => void publish(row)}
          >
            <Button
              size="small"
              type="link"
              icon={<CloudUploadOutlined />}
              disabled={row.is_published || !canPublish}
              loading={publishing}
            >
              نشر
            </Button>
          </Popconfirm>
          <Popconfirm
            title={`حذف «${row.name}»؟`}
            okText="حذف"
            cancelText="إلغاء"
            disabled={row.is_published}
            onConfirm={() => void remove(row)}
          >
            <Button
              size="small"
              type="link"
              danger
              icon={<DeleteOutlined />}
              disabled={row.is_published}
            >
              حذف
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const matrixColumns = [
    { title: 'الرقم الجامعي', dataIndex: 'university_id', width: 130, fixed: 'right' as const },
    { title: 'الاسم', dataIndex: 'full_name_ar', width: 200, fixed: 'right' as const },
    ...(data?.assessments ?? []).map((assessment) => ({
      title: (
        <Space direction="vertical" size={0}>
          <Text strong={!assessment.is_published}>
            {assessment.is_published && <LockOutlined style={{ marginInlineEnd: 4 }} />}
            {assessment.name}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            /{assessment.max_score} ×{assessment.weight}
          </Text>
        </Space>
      ),
      key: assessment.assessment_id,
      width: 130,
      render: (_: unknown, student: StudentGradeRow) => {
        const value = cellValue(assessment.assessment_id, student);
        const changed =
          edits[assessment.assessment_id] !== undefined &&
          Object.prototype.hasOwnProperty.call(
            edits[assessment.assessment_id],
            student.student_id,
          ) &&
          value !== (student.scores[assessment.assessment_id] ?? null);
        return (
          <InputNumber
            size="small"
            min={0}
            max={Number(assessment.max_score)}
            value={value}
            disabled={assessment.is_published}
            status={changed ? 'warning' : undefined}
            style={{ width: '100%' }}
            onChange={(next) => setCell(assessment.assessment_id, student.student_id, next)}
          />
        );
      },
    })),
    {
      title: 'المجموع الموزون',
      key: 'total',
      width: 130,
      render: (_: unknown, student: StudentGradeRow) => (
        <Text strong>{student.weighted_total}</Text>
      ),
    },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      {notice && (
        <Alert
          closable
          showIcon
          type={notice.kind}
          message={notice.text}
          description={notice.hint}
          onClose={() => setNotice(null)}
        />
      )}

      <Card
        title="المادة"
        extra={
          <Space>
            <Select
              showSearch
              optionFilterProp="label"
              style={{ minWidth: 360 }}
              placeholder="اختر المادة"
              value={offeringId}
              onChange={(value) => {
                void (async () => {
                  if (await canDiscard('تغيير المادة')) setOfferingId(value);
                })();
              }}
              options={offerings.map((item) => ({
                value: item.offering_id,
                label: `${item.course_code} — ${item.course_name_ar} (${item.group_name} · المرحلة ${item.stage} · ${studyLabel[item.study_type] ?? item.study_type})`,
              }))}
            />
            <Button
              icon={<ReloadOutlined />}
              disabled={!offeringId}
              loading={loading}
              onClick={() =>
                void (async () => {
                  if (!offeringId) return;
                  if (await canDiscard('التحديث')) await load(offeringId);
                })()
              }
            >
              تحديث
            </Button>
            <Button icon={<DownloadOutlined />} disabled={!data} onClick={() => void exportFile()}>
              تصدير Excel
            </Button>
          </Space>
        }
      >
        {data ? (
          <Row gutter={16}>
            <Col span={6}>
              <Statistic title="الطلاب المسجّلون" value={data.students.length} />
            </Col>
            <Col span={6}>
              <Statistic title="التقييمات" value={data.assessments.length} />
            </Col>
            <Col span={6}>
              <Statistic
                title="مجموع الأوزان"
                value={weightUsed}
                suffix="/ 100"
                valueStyle={{ color: weightUsed > 100 ? '#a8071a' : undefined }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="تقييمات منشورة"
                value={data.assessments.filter((item) => item.is_published).length}
              />
            </Col>
          </Row>
        ) : (
          <Paragraph type="secondary" style={{ margin: 0 }}>
            اختر مادة لعرض تقييماتها ومصفوفة درجاتها. مدير الكلية يرى كل مواد الكلية.
          </Paragraph>
        )}
      </Card>

      <Card title="التقييمات">
        <Table<Assessment>
          size="small"
          rowKey="assessment_id"
          loading={loading}
          dataSource={data?.assessments ?? []}
          columns={assessmentColumns}
          pagination={false}
          locale={{ emptyText: 'لا تقييمات بعد — أضف أول تقييم من النموذج أدناه' }}
        />

        <Divider orientation="right">تقييم جديد</Divider>

        <Form<AssessmentFormValues>
          form={form}
          layout="inline"
          onFinish={(values) => void create(values)}
          initialValues={{ kind: 'quiz', max_score: 100, weight: 10 }}
          style={{ rowGap: 12 }}
        >
          <Form.Item
            name="name"
            label="الاسم"
            rules={[
              { required: true, message: 'أدخل اسم التقييم' },
              { min: 2, message: 'الاسم قصير جداً' },
            ]}
          >
            <Input placeholder="كويز أول" maxLength={200} style={{ width: 220 }} />
          </Form.Item>
          <Form.Item name="kind" label="النوع">
            <Select
              style={{ width: 150 }}
              options={Object.entries(assessmentKindLabel).map(([value, label]) => ({
                value,
                label,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="max_score"
            label="الدرجة العظمى"
            rules={[{ required: true, message: 'أدخل الدرجة العظمى' }]}
          >
            <InputNumber min={0.5} max={1000} step={5} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item
            name="weight"
            label="الوزن"
            rules={[{ required: true, message: 'أدخل الوزن' }]}
          >
            <InputNumber min={0} max={100} step={5} style={{ width: 100 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<PlusOutlined />} loading={saving}>
              إضافة
            </Button>
          </Form.Item>
        </Form>

        <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
          مجموع الأوزان الحالي {weightUsed} من 100 — يرفض الخادم أي تقييم يتجاوز به المجموع 100.
          {!canPublish && ' النشر متاح لمدير الكلية فقط؛ يمكنك إدخال المسودات وحفظها.'}
        </Paragraph>
      </Card>

      <Card
        title="مصفوفة الدرجات"
        extra={
          <Space>
            <Text type="secondary">
              {dirtyAssessmentIds.length > 0
                ? `${dirtyAssessmentIds.length} تقييم فيه تعديلات غير محفوظة`
                : 'لا تعديلات غير محفوظة'}
            </Text>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              loading={saving}
              disabled={!data || dirtyAssessmentIds.length === 0}
              onClick={() => void save()}
            >
              حفظ الدرجات
            </Button>
          </Space>
        }
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="الدرجات تُحفظ كمسودات أولاً، والنشر يوقف التعديل نهائياً (يعيد الخادم 409 للمحاولة)."
          description="الخلايا المقفلة تخصّ تقييماً منشوراً. لا يمكن حذف درجة بعد إدخالها — استبدلها بقيمة أخرى قبل النشر. إفراغ خلية يلغي تعديلها ويعيد القيمة المحفوظة."
        />

        <Table<StudentGradeRow>
          size="small"
          rowKey="student_id"
          loading={loading}
          dataSource={data?.students ?? []}
          columns={matrixColumns}
          pagination={{ pageSize: 25, hideOnSinglePage: true }}
          scroll={{ x: 'max-content' }}
          locale={{
            emptyText: data
              ? 'لا طلاب مسجّلين في هذه المادة بعد'
              : 'اختر مادة لعرض المصفوفة',
          }}
        />
      </Card>
    </Space>
  );
}
