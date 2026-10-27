import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import {
  CopyOutlined,
  KeyOutlined,
  MobileOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  ApiError,
  listAdminUsers,
  listDepartments,
  resetUserDevice,
  resetUserPassword,
  resetUserTotp,
  type AdminUserRow,
  type Department,
} from '../api';

const { Text } = Typography;

const PAGE_SIZE = 20;

const roleLabel: Record<string, string> = {
  college_admin: 'مدير الكلية',
  department_head: 'رئيس قسم',
  instructor: 'تدريسي',
  student: 'طالب',
};

const roleColor: Record<string, string> = {
  college_admin: 'purple',
  department_head: 'geekblue',
  instructor: 'cyan',
  student: 'blue',
};

const statusLabel: Record<string, string> = {
  pending: 'بانتظار التفعيل',
  active: 'مفعّل',
  disabled: 'معطّل',
};

const statusColor: Record<string, string> = {
  pending: 'gold',
  active: 'green',
  disabled: 'red',
};

interface Secret {
  universityId: string;
  fullName: string;
  password: string;
}

/** نسخ إلى الحافظة مع بديل للمتصفحات التي تمنع الحافظة خارج HTTPS. */
async function copyText(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // ننتقل إلى الطريقة البديلة
  }
  try {
    const area = document.createElement('textarea');
    area.value = text;
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    const copied = document.execCommand('copy');
    document.body.removeChild(area);
    return copied;
  } catch {
    return false;
  }
}

function failureText(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

export default function UsersPage() {
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState('');
  const [role, setRole] = useState<string | undefined>();
  const [department, setDepartment] = useState<string | undefined>();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [secret, setSecret] = useState<Secret | null>(null);

  useEffect(() => {
    listDepartments()
      .then(setDepartments)
      .catch(() => message.error('تعذّر تحميل قائمة الأقسام'));
  }, []);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const res = await listAdminUsers({
        q,
        role,
        department_code: department,
        page,
        limit: PAGE_SIZE,
      });
      setRows(res.items);
      setTotal(res.total);
    } catch (e) {
      message.error(failureText(e, 'تعذّر تحميل قائمة المستخدمين'));
    } finally {
      setLoading(false);
    }
  }, [q, role, department, page]);

  useEffect(() => {
    void load();
  }, [load]);

  const resetDevice = async (row: AdminUserRow): Promise<void> => {
    setBusy(`device:${row.university_id}`);
    try {
      const res = await resetUserDevice(row.university_id);
      message.success(
        res.devices_revoked > 0
          ? `أُلغي ربط ${res.devices_revoked} جهاز وأُنهيت ${res.sessions_revoked} جلسة`
          : `لا جهاز مرتبط بهذا المستخدم؛ أُنهيت ${res.sessions_revoked} جلسة`,
      );
      await load();
    } catch (e) {
      message.error(failureText(e, 'تعذّر إعادة ضبط جهاز المستخدم'));
    } finally {
      setBusy(null);
    }
  };

  const resetPassword = async (row: AdminUserRow): Promise<void> => {
    setBusy(`password:${row.university_id}`);
    try {
      const res = await resetUserPassword(row.university_id);
      // تُعرض مرة واحدة فقط: تُمسح من الحالة عند إغلاق النافذة
      setSecret({
        universityId: row.university_id,
        fullName: row.full_name_ar,
        password: res.temporary_password,
      });
      await load();
    } catch (e) {
      message.error(failureText(e, 'تعذّر إعادة ضبط كلمة المرور'));
    } finally {
      setBusy(null);
    }
  };

  const resetTotp = async (row: AdminUserRow): Promise<void> => {
    setBusy(`totp:${row.university_id}`);
    try {
      const res = await resetUserTotp(row.university_id);
      message.success(
        res.was_enabled
          ? 'أُعيد ضبط التحقق بخطوتين؛ يسجّل الدخول بكلمة المرور ثم يعيد الإعداد'
          : 'التحقق بخطوتين لم يكن مفعّلاً لهذا الحساب',
      );
      await load();
    } catch (e) {
      message.error(failureText(e, 'تعذّر إعادة ضبط التحقق بخطوتين'));
    } finally {
      setBusy(null);
    }
  };

  const copyPassword = async (): Promise<void> => {
    if (!secret) return;
    const copied = await copyText(secret.password);
    if (copied) message.success('نُسخت كلمة المرور إلى الحافظة');
    else message.error('تعذّر النسخ التلقائي — انسخ كلمة المرور يدوياً قبل الإغلاق');
  };

  const columns: ColumnsType<AdminUserRow> = [
    { title: 'الرقم الجامعي', dataIndex: 'university_id', width: 130 },
    { title: 'الاسم', dataIndex: 'full_name_ar' },
    {
      title: 'القسم',
      dataIndex: 'department_name_ar',
      width: 170,
      render: (name: string | null, row) =>
        name ? `${name} (${row.department_code})` : '—',
    },
    {
      title: 'الشعبة',
      dataIndex: 'group_name',
      width: 90,
      render: (value: string | null) => value ?? '—',
    },
    {
      title: 'الدور',
      dataIndex: 'role',
      width: 120,
      render: (value: string) => (
        <Tag color={roleColor[value] ?? 'default'}>{roleLabel[value] ?? value}</Tag>
      ),
    },
    {
      title: 'الحالة',
      dataIndex: 'status',
      width: 130,
      render: (value: string) => (
        <Tag color={statusColor[value] ?? 'default'}>{statusLabel[value] ?? value}</Tag>
      ),
    },
    {
      title: 'كلمة المرور',
      dataIndex: 'must_change_password',
      width: 120,
      render: (value: boolean) =>
        value ? <Tag color="gold">تغيير مطلوب</Tag> : <Tag>دائمة</Tag>,
    },
    {
      title: 'الجهاز',
      dataIndex: 'device_status',
      width: 110,
      render: (value: AdminUserRow['device_status']) =>
        value === 'active' ? (
          <Tag color="green">مرتبط</Tag>
        ) : (
          <Tag>غير مرتبط</Tag>
        ),
    },
    {
      title: 'إجراءات',
      key: 'actions',
      width: 300,
      render: (_: unknown, row: AdminUserRow) => {
        const deviceBusy = busy === `device:${row.university_id}`;
        const passwordBusy = busy === `password:${row.university_id}`;
        const disabled = busy !== null;
        return (
          <Space size={4}>
            <Popconfirm
              title={`إعادة ضبط جهاز «${row.full_name_ar}»؟`}
              description="سيُلغى ربط كل أجهزة المستخدم وتُنهى جلساته، ويستطيع الدخول من جهاز جديد."
              okText="تأكيد"
              cancelText="إلغاء"
              onConfirm={() => void resetDevice(row)}
            >
              <Button
                size="small"
                type="link"
                icon={<MobileOutlined />}
                disabled={disabled}
                loading={deviceBusy}
              >
                الجهاز
              </Button>
            </Popconfirm>
            <Button
              size="small"
              type="link"
              icon={<KeyOutlined />}
              disabled={disabled}
              loading={passwordBusy}
              onClick={() => void resetPassword(row)}
            >
              كلمة المرور
            </Button>
            <Popconfirm
              title={`إعادة ضبط التحقق بخطوتين لـ«${row.full_name_ar}»؟`}
              description="استخدمها عند فقدان هاتف التدريسي. يُلغى السرّ ويُطلب منه إعادة الإعداد."
              okText="تأكيد"
              cancelText="إلغاء"
              onConfirm={() => void resetTotp(row)}
            >
              <Button
                size="small"
                type="link"
                icon={<SafetyCertificateOutlined />}
                disabled={disabled}
                loading={busy === `totp:${row.university_id}`}
              >
                التحقق
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <>
      <Card
        title="المستخدمون"
        extra={
          <Button icon={<ReloadOutlined />} onClick={() => void load()} loading={loading}>
            تحديث
          </Button>
        }
      >
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
            placeholder="الدور"
            style={{ width: 160 }}
            value={role}
            onChange={(value) => {
              setPage(1);
              setRole(value);
            }}
            options={Object.entries(roleLabel).map(([value, label]) => ({ value, label }))}
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
          <Text type="secondary">{total} مستخدم</Text>
        </Space>

        <Table<AdminUserRow>
          size="middle"
          rowKey="user_id"
          loading={loading}
          dataSource={rows}
          columns={columns}
          scroll={{ x: 1100 }}
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total,
            showSizeChanger: false,
            onChange: (nextPage) => setPage(nextPage),
          }}
          locale={{ emptyText: 'لا يوجد مستخدمون مطابقون لهذا الترشيح' }}
        />
      </Card>

      <Modal
        open={secret !== null}
        title="كلمة مرور مؤقتة"
        okText="حفظتها — إغلاق"
        cancelButtonProps={{ style: { display: 'none' } }}
        maskClosable={false}
        destroyOnClose
        onOk={() => setSecret(null)}
        onCancel={() => setSecret(null)}
      >
        {secret && (
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Alert
              type="warning"
              showIcon
              message="تُعرض مرة واحدة فقط"
              description="لن تُخزَّن هنا ولن يمكن استرجاعها بعد إغلاق النافذة. انسخها وسلّمها للمستخدم، وسيُطلب منه تغييرها عند أول دخول."
            />
            <Text>
              المستخدم: {secret.fullName} ({secret.universityId})
            </Text>
            <Space.Compact style={{ width: '100%' }}>
              <Input readOnly value={secret.password} style={{ direction: 'ltr' }} />
              <Button icon={<CopyOutlined />} onClick={() => void copyPassword()}>
                نسخ
              </Button>
            </Space.Compact>
          </Space>
        )}
      </Modal>
    </>
  );
}
