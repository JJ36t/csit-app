import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  Popconfirm,
  Row,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { DeleteOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import {
  ApiError,
  createAnnouncement,
  deleteAnnouncement,
  listAdminAnnouncements,
  listDepartments,
  listOfferings,
  type AdminAnnouncement,
  type AnnouncementInput,
  type Department,
  type Offering,
} from '../api';

const { Text, Paragraph } = Typography;

const scopeLabel: Record<string, string> = {
  college: 'الكلية',
  department: 'قسم',
  stage: 'مرحلة',
  offering: 'مادة',
  group: 'شعبة',
};

const priorityLabel: Record<string, string> = { normal: 'عادية', high: 'مهمة' };
const priorityColor: Record<string, string> = { normal: 'default', high: 'red' };

const statusLabel: Record<string, string> = {
  scheduled: 'مجدول',
  active: 'نشط',
  expired: 'منتهٍ',
};
const statusColor: Record<string, string> = {
  scheduled: 'blue',
  active: 'green',
  expired: 'default',
};

const STAGES = [1, 2, 3, 4, 5, 6];

/** توقيت بغداد للعرض فقط — التخزين في الخادم UTC. */
const baghdadDateTime = (iso: string): string =>
  new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Baghdad',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(iso));

interface AnnouncementFormValues {
  scope: string;
  department_id?: string;
  stage?: number;
  offering_id?: string;
  title: string;
  body: string;
  priority: string;
  pinned: boolean;
  publish_at?: Dayjs;
  expires_at?: Dayjs;
}

interface Notice {
  kind: 'success' | 'error' | 'info';
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

export default function AnnouncementsPage() {
  const [items, setItems] = useState<AdminAnnouncement[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [offerings, setOfferings] = useState<Offering[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [form] = Form.useForm<AnnouncementFormValues>();
  const scope = Form.useWatch('scope', form);

  const departmentName = useMemo(() => {
    const map: Record<string, string> = {};
    departments.forEach((item) => {
      map[item.id] = item.name_ar;
    });
    return map;
  }, [departments]);

  const offeringById = useMemo(() => {
    const map: Record<string, Offering> = {};
    offerings.forEach((item) => {
      map[item.offering_id] = item;
    });
    return map;
  }, [offerings]);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const res = await listAdminAnnouncements();
      setItems(res.items);
    } catch (error) {
      setNotice(failureText(error, 'تعذّر تحميل الإعلانات'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    listDepartments()
      .then(setDepartments)
      .catch(() => message.error('تعذّر تحميل قائمة الأقسام'));
    listOfferings()
      .then((res) => setOfferings(res.items))
      .catch(() => message.error('تعذّر تحميل قائمة المواد'));
  }, []);

  const submit = async (values: AnnouncementFormValues): Promise<void> => {
    setSaving(true);
    setNotice(null);
    const payload: AnnouncementInput = {
      scope: values.scope,
      scope_id:
        values.scope === 'college'
          ? null
          : values.scope === 'offering'
            ? values.offering_id ?? null
            : values.department_id ?? null,
      stage: values.scope === 'stage' ? values.stage ?? null : null,
      title: values.title.trim(),
      body: values.body.trim(),
      priority: values.priority,
      pinned: values.pinned ?? false,
      publish_at: values.publish_at ? values.publish_at.toISOString() : null,
      expires_at: values.expires_at ? values.expires_at.toISOString() : null,
    };
    try {
      await createAnnouncement(payload);
      const scheduled = values.publish_at ? values.publish_at.toDate() > new Date() : false;
      setNotice({
        kind: 'success',
        text: scheduled
          ? `أُضيف الإعلان «${payload.title}» مجدولاً — لا يظهر للطلاب قبل موعد النشر`
          : `أُضيف الإعلان «${payload.title}» ونُشر للمستهدفين`,
      });
      form.resetFields();
      await load();
    } catch (error) {
      setNotice(failureText(error, 'تعذّر إنشاء الإعلان'));
    } finally {
      setSaving(false);
    }
  };

  const remove = async (row: AdminAnnouncement): Promise<void> => {
    setDeletingId(row.announcement_id);
    setNotice(null);
    try {
      await deleteAnnouncement(row.announcement_id);
      setNotice({ kind: 'success', text: `حُذف الإعلان «${row.title}»` });
      await load();
    } catch (error) {
      setNotice(failureText(error, 'تعذّر حذف الإعلان'));
    } finally {
      setDeletingId(null);
    }
  };

  const scopeText = (row: AdminAnnouncement): string => {
    if (row.scope === 'college' || !row.scope_id) return 'الكلية';
    if (row.scope === 'department') {
      return `قسم ${departmentName[row.scope_id] ?? 'غير معروف'}`;
    }
    if (row.scope === 'stage') {
      const name = departmentName[row.scope_id] ?? 'غير معروف';
      return `المرحلة ${row.stage ?? '—'} · ${name}`;
    }
    if (row.scope === 'offering') {
      const offering = offeringById[row.scope_id];
      return offering
        ? `${offering.course_code} — ${offering.course_name_ar} (${offering.group_name})`
        : 'مادة خارج قائمتك';
    }
    return `${scopeLabel[row.scope] ?? row.scope} · ${row.scope_id.slice(0, 8)}`;
  };

  const columns = [
    {
      title: 'العنوان',
      key: 'title',
      render: (_: unknown, row: AdminAnnouncement) => (
        <Space direction="vertical" size={0}>
          <Text strong>{row.title}</Text>
          <Text type="secondary" style={{ fontSize: 12 }} ellipsis>
            {row.body}
          </Text>
        </Space>
      ),
    },
    {
      title: 'النطاق',
      key: 'scope',
      width: 240,
      render: (_: unknown, row: AdminAnnouncement) => (
        <Space direction="vertical" size={0}>
          <Tag>{scopeLabel[row.scope] ?? row.scope}</Tag>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {scopeText(row)}
          </Text>
        </Space>
      ),
    },
    {
      title: 'الحالة',
      dataIndex: 'status',
      width: 100,
      render: (value: string) => (
        <Tag color={statusColor[value] ?? 'default'}>{statusLabel[value] ?? value}</Tag>
      ),
    },
    {
      title: 'الأولوية',
      dataIndex: 'priority',
      width: 100,
      render: (value: string) => (
        <Tag color={priorityColor[value] ?? 'default'}>{priorityLabel[value] ?? value}</Tag>
      ),
    },
    {
      title: 'التثبيت',
      dataIndex: 'pinned',
      width: 90,
      render: (value: boolean) => (value ? <Tag color="gold">مثبّت</Tag> : '—'),
    },
    {
      title: 'الجدولة',
      key: 'schedule',
      width: 190,
      render: (_: unknown, row: AdminAnnouncement) => (
        <Space direction="vertical" size={0}>
          <Text style={{ fontSize: 12 }}>
            النشر: {row.publish_at ? baghdadDateTime(row.publish_at) : 'فوري'}
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            الانتهاء: {row.expires_at ? baghdadDateTime(row.expires_at) : 'بلا حد'}
          </Text>
        </Space>
      ),
    },
    {
      title: 'إجراءات',
      key: 'actions',
      width: 110,
      render: (_: unknown, row: AdminAnnouncement) => (
        <Popconfirm
          title={`حذف «${row.title}»؟`}
          description="سيختفي الإعلان من اللوحة ومن خلاصة المستخدمين."
          okText="حذف"
          cancelText="إلغاء"
          okButtonProps={{ danger: true }}
          onConfirm={() => void remove(row)}
        >
          <Button
            size="small"
            type="link"
            danger
            icon={<DeleteOutlined />}
            loading={deletingId === row.announcement_id}
          >
            حذف
          </Button>
        </Popconfirm>
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
        title="الإعلانات"
        extra={
          <Button icon={<ReloadOutlined />} onClick={() => void load()} loading={loading}>
            تحديث
          </Button>
        }
      >
        <Paragraph type="secondary" style={{ marginTop: 0 }}>
          تعرض القائمة المجدولة والمنتهية أيضاً (لا الموجّهة فقط). رئيس القسم يرى إعلانات الكلية
          وإعلانات قسمه.
        </Paragraph>
        <Table<AdminAnnouncement>
          size="small"
          rowKey="announcement_id"
          loading={loading}
          dataSource={items}
          columns={columns}
          scroll={{ x: 'max-content' }}
          pagination={{ pageSize: 10, hideOnSinglePage: true }}
          locale={{ emptyText: 'لا إعلانات بعد — أنشئ أول إعلان من النموذج أدناه' }}
        />
      </Card>

      <Card title="إعلان جديد">
        <Form<AnnouncementFormValues>
          form={form}
          layout="vertical"
          onFinish={(values) => void submit(values)}
          initialValues={{ scope: 'college', priority: 'normal', pinned: false }}
        >
          <Row gutter={12}>
            <Col xs={24} md={8}>
              <Form.Item
                name="scope"
                label="النطاق"
                rules={[{ required: true, message: 'اختر النطاق' }]}
              >
                <Select
                  style={{ width: '100%' }}
                  options={[
                    { value: 'college', label: 'الكلية (الجميع)' },
                    { value: 'department', label: 'قسم' },
                    { value: 'stage', label: 'مرحلة داخل قسم' },
                    { value: 'offering', label: 'مادة' },
                  ]}
                />
              </Form.Item>
            </Col>

            {(scope === 'department' || scope === 'stage') && (
              <Col xs={24} md={8}>
                <Form.Item
                  name="department_id"
                  label="القسم"
                  rules={[{ required: true, message: 'اختر القسم' }]}
                >
                  <Select
                    showSearch
                    optionFilterProp="label"
                    placeholder="اختر القسم المستهدف"
                    style={{ width: '100%' }}
                    options={departments.map((item) => ({
                      value: item.id,
                      label: `${item.name_ar} (${item.code})`,
                    }))}
                  />
                </Form.Item>
              </Col>
            )}

            {scope === 'stage' && (
              <Col xs={24} md={8}>
                <Form.Item
                  name="stage"
                  label="المرحلة"
                  rules={[{ required: true, message: 'اختر المرحلة' }]}
                >
                  <Select
                    style={{ width: '100%' }}
                    placeholder="اختر المرحلة"
                    options={STAGES.map((value) => ({ value, label: `المرحلة ${value}` }))}
                  />
                </Form.Item>
              </Col>
            )}

            {scope === 'offering' && (
              <Col xs={24} md={16}>
                <Form.Item
                  name="offering_id"
                  label="المادة"
                  rules={[{ required: true, message: 'اختر المادة' }]}
                >
                  <Select
                    showSearch
                    optionFilterProp="label"
                    placeholder="اختر مادة من موادك"
                    style={{ width: '100%' }}
                    options={offerings.map((item) => ({
                      value: item.offering_id,
                      label: `${item.course_code} — ${item.course_name_ar} (${item.group_name} · المرحلة ${item.stage})`,
                    }))}
                  />
                </Form.Item>
              </Col>
            )}
          </Row>

          <Form.Item
            name="title"
            label="العنوان"
            rules={[
              { required: true, message: 'أدخل عنوان الإعلان' },
              { min: 3, message: 'العنوان قصير جداً' },
            ]}
          >
            <Input placeholder="مثال: تعديل موعد امتحان الشبكات" maxLength={300} />
          </Form.Item>

          <Form.Item
            name="body"
            label="النص"
            rules={[{ required: true, message: 'أدخل نص الإعلان' }]}
          >
            <Input.TextArea rows={4} maxLength={5000} showCount placeholder="نص الإعلان…" />
          </Form.Item>

          <Row gutter={12}>
            <Col xs={24} md={6}>
              <Form.Item name="priority" label="الأولوية">
                <Select
                  style={{ width: '100%' }}
                  options={[
                    { value: 'normal', label: 'عادية' },
                    { value: 'high', label: 'مهمة' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={6}>
              <Form.Item
                name="pinned"
                label="التثبيت"
                valuePropName="checked"
                tooltip="الإعلان المثبّت يظهر أول القائمة"
              >
                <Switch checkedChildren="مثبّت" unCheckedChildren="عادي" />
              </Form.Item>
            </Col>
            <Col xs={24} md={6}>
              <Form.Item
                name="publish_at"
                label="بدء النشر"
                tooltip="اتركه فارغاً للنشر الفوري"
              >
                <DatePicker
                  showTime
                  format="YYYY-MM-DD HH:mm"
                  style={{ width: '100%' }}
                  placeholder="فوري"
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={6}>
              <Form.Item
                name="expires_at"
                label="نهاية النشر"
                tooltip="اتركه فارغاً لبلا حد"
                rules={[
                  {
                    validator: async (_rule, value: Dayjs | undefined) => {
                      const publishAt = form.getFieldValue('publish_at') as Dayjs | undefined;
                      if (!value || !publishAt) return;
                      if (!value.isAfter(publishAt)) {
                        throw new Error('تاريخ الانتهاء يجب أن يكون بعد تاريخ النشر');
                      }
                    },
                  },
                ]}
              >
                <DatePicker
                  showTime
                  format="YYYY-MM-DD HH:mm"
                  style={{ width: '100%' }}
                  placeholder="بلا حد"
                />
              </Form.Item>
            </Col>
          </Row>

          <Button type="primary" htmlType="submit" icon={<PlusOutlined />} loading={saving}>
            إنشاء الإعلان
          </Button>
        </Form>
      </Card>
    </Space>
  );
}
