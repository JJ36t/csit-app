import { useCallback, useEffect, useState } from 'react';
import {
  Button,
  Card,
  Drawer,
  Input,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { ReloadOutlined, SendOutlined } from '@ant-design/icons';
import {
  ApiError,
  getAdminRequest,
  listAdminRequests,
  replyAdminRequest,
  updateAdminRequest,
  type AdminRequestDetail,
  type AdminRequestRow,
} from '../api';

const { Text, Paragraph } = Typography;

const statusLabels: Record<string, string> = {
  open: 'مفتوح',
  in_progress: 'قيد المعالجة',
  resolved: 'تم الحل',
  closed: 'مغلق',
};

const statusColors: Record<string, string> = {
  open: 'blue',
  in_progress: 'gold',
  resolved: 'green',
  closed: 'default',
};

/// طلبات الطلبة: خيط محادثة + تغيير حالة. الإسناد عبر «إسناد إليّ».
export default function RequestsPage() {
  const [status, setStatus] = useState<string>('open');
  const [items, setItems] = useState<AdminRequestRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<AdminRequestDetail | null>(null);
  const [reply, setReply] = useState('');
  const [sending, setSending] = useState(false);

  const load = useCallback(async (next = status) => {
    setLoading(true);
    try {
      const data = await listAdminRequests(next);
      setItems(data.items);
    } catch (error) {
      message.error(error instanceof ApiError ? error.message : 'تعذّر تحميل الطلبات');
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const open = async (id: string): Promise<void> => {
    try {
      setDetail(await getAdminRequest(id));
      setReply('');
    } catch (error) {
      message.error(error instanceof ApiError ? error.message : 'تعذّر فتح الطلب');
    }
  };

  const send = async (): Promise<void> => {
    if (!detail || reply.trim().length === 0) return;
    setSending(true);
    try {
      setDetail(await replyAdminRequest(detail.request_id, reply.trim()));
      setReply('');
      await load();
    } catch (error) {
      message.error(error instanceof ApiError ? error.message : 'تعذّر إرسال الرد');
    } finally {
      setSending(false);
    }
  };

  const change = async (patch: { status?: string }): Promise<void> => {
    if (!detail) return;
    try {
      const updated = await updateAdminRequest(detail.request_id, patch);
      setDetail(updated);
      await load();
      message.success('حُدّث الطلب');
    } catch (error) {
      message.error(error instanceof ApiError ? error.message : 'تعذّر تحديث الطلب');
    }
  };

  return (
    <Card
      title="طلبات الطلبة"
      extra={
        <Space>
          <Select
            value={status}
            style={{ width: 150 }}
            onChange={setStatus}
            options={[
              { value: 'open', label: 'مفتوح' },
              { value: 'in_progress', label: 'قيد المعالجة' },
              { value: 'resolved', label: 'تم الحل' },
              { value: 'closed', label: 'مغلق' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={() => void load()} loading={loading}>
            تحديث
          </Button>
        </Space>
      }
    >
      <Table<AdminRequestRow>
        rowKey="request_id"
        size="small"
        loading={loading}
        dataSource={items}
        pagination={{ pageSize: 12, hideOnSinglePage: true }}
        onRow={(row) => ({ onClick: () => void open(row.request_id) })}
        columns={[
          { title: 'الموضوع', dataIndex: 'subject' },
          { title: 'التصنيف', dataIndex: 'category_label', width: 150 },
          {
            title: 'الحالة',
            dataIndex: 'status',
            width: 110,
            render: (value: string) => (
              <Tag color={statusColors[value]}>{statusLabels[value] ?? value}</Tag>
            ),
          },
          {
            title: 'آخر تحديث',
            dataIndex: 'updated_at',
            width: 170,
            render: (value: string | null) => (value ? value.slice(0, 16).replace('T', ' ') : '—'),
          },
        ]}
      />

      <Drawer
        open={detail !== null}
        onClose={() => setDetail(null)}
        width={560}
        title={detail?.subject}
        extra={
          detail && (
            <Space>
              <Select
                size="small"
                value={detail.status}
                style={{ width: 130 }}
                onChange={(value) => void change({ status: value })}
                options={Object.entries(statusLabels).map(([value, label]) => ({
                  value,
                  label,
                }))}
              />
            </Space>
          )
        }
      >
        {detail && (
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Text type="secondary">
              {detail.category_label} · {statusLabels[detail.status] ?? detail.status}
            </Text>
            {detail.messages.map((item) => (
              <Card key={item.message_id} size="small">
                <Paragraph style={{ marginBottom: 4 }}>{item.body}</Paragraph>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {item.created_at ? item.created_at.slice(0, 16).replace('T', ' ') : ''}
                </Text>
              </Card>
            ))}
            {detail.status === 'resolved' || detail.status === 'closed' ? (
              <Text type="secondary">الطلب مغلق — لا يمكن إضافة رسائل.</Text>
            ) : (
              <Space.Compact style={{ width: '100%' }}>
                <Input
                  value={reply}
                  onChange={(event) => setReply(event.target.value)}
                  placeholder="اكتب ردك على الطالب…"
                  onPressEnter={() => void send()}
                />
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  loading={sending}
                  onClick={() => void send()}
                >
                  إرسال
                </Button>
              </Space.Compact>
            )}
          </Space>
        )}
      </Drawer>
    </Card>
  );
}
