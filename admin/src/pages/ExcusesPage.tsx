import { useCallback, useEffect, useState } from 'react';
import {
  Button,
  Card,
  Input,
  Modal,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd';
import { CheckOutlined, CloseOutlined, ReloadOutlined } from '@ant-design/icons';
import {
  ApiError,
  listAdminExcuses,
  reviewExcuse,
  type AdminExcuse,
} from '../api';

const { Text, Paragraph } = Typography;

const statusColors: Record<string, string> = {
  pending: 'gold',
  approved: 'green',
  rejected: 'red',
};

const statusLabels: Record<string, string> = {
  pending: 'قيد المراجعة',
  approved: 'مقبول',
  rejected: 'مرفوض',
};

/// مراجعة الأعذار: القبول يحوّل سجل الحضور إلى «بعذر» على الخادم ويُشعر الطالب.
export default function ExcusesPage() {
  const [status, setStatus] = useState('pending');
  const [items, setItems] = useState<AdminExcuse[]>([]);
  const [pendingTotal, setPendingTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [reviewing, setReviewing] = useState<AdminExcuse | null>(null);
  const [approve, setApprove] = useState(true);
  const [note, setNote] = useState('');

  const load = useCallback(async (next = status) => {
    setLoading(true);
    try {
      const data = await listAdminExcuses(next);
      setItems(data.items);
      setPendingTotal(data.pending_total);
    } catch (error) {
      message.error(error instanceof ApiError ? error.message : 'تعذّر تحميل الأعذار');
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const submit = async (): Promise<void> => {
    if (!reviewing) return;
    try {
      await reviewExcuse(reviewing.excuse_id, approve, note);
      message.success(approve ? 'قُبل العذر وحُدّث الحضور' : 'رُفض العذر');
      setReviewing(null);
      setNote('');
      await load();
    } catch (error) {
      message.error(error instanceof ApiError ? error.message : 'تعذّر تسجيل القرار');
    }
  };

  return (
    <Card
      title={`مراجعة الأعذار — بانتظار المراجعة: ${pendingTotal}`}
      extra={
        <Button icon={<ReloadOutlined />} onClick={() => void load()} loading={loading}>
          تحديث
        </Button>
      }
    >
      <Tabs
        activeKey={status}
        onChange={setStatus}
        items={[
          { key: 'pending', label: 'قيد المراجعة' },
          { key: 'approved', label: 'مقبولة' },
          { key: 'rejected', label: 'مرفوضة' },
        ]}
      />
      <Table<AdminExcuse>
        rowKey="excuse_id"
        size="small"
        loading={loading}
        dataSource={items}
        pagination={{ pageSize: 12, hideOnSinglePage: true }}
        columns={[
          {
            title: 'الطالب',
            render: (_, row) => (
              <Space direction="vertical" size={0}>
                <Text strong>{row.student_name_ar ?? '—'}</Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {row.session_date}
                </Text>
              </Space>
            ),
          },
          {
            title: 'المادة',
            render: (_, row) => `${row.course_code} — ${row.course_name_ar}`,
          },
          {
            title: 'السبب',
            render: (_, row) => (
              <Paragraph style={{ margin: 0, maxWidth: 320 }} ellipsis={{ rows: 2 }}>
                {row.reason}
              </Paragraph>
            ),
          },
          {
            title: 'المرفق',
            width: 110,
            render: (_, row) =>
              row.attachment ? (
                <a href={row.attachment.download_url} target="_blank" rel="noreferrer">
                  فتح
                </a>
              ) : (
                <Text type="secondary">—</Text>
              ),
          },
          {
            title: 'الحالة',
            width: 110,
            render: (_, row) => (
              <Tag color={statusColors[row.status]}>{statusLabels[row.status]}</Tag>
            ),
          },
          {
            title: 'إجراء',
            width: 210,
            render: (_, row) =>
              row.status === 'pending' ? (
                <Space size={4}>
                  <Button
                    size="small"
                    type="primary"
                    icon={<CheckOutlined />}
                    onClick={() => {
                      setReviewing(row);
                      setApprove(true);
                      setNote('');
                    }}
                  >
                    قبول
                  </Button>
                  <Button
                    size="small"
                    danger
                    icon={<CloseOutlined />}
                    onClick={() => {
                      setReviewing(row);
                      setApprove(false);
                      setNote('');
                    }}
                  >
                    رفض
                  </Button>
                </Space>
              ) : (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {row.review_note ?? '—'}
                </Text>
              ),
          },
        ]}
      />

      <Modal
        open={reviewing !== null}
        title={`${approve ? 'قبول' : 'رفض'} عذر: ${reviewing?.student_name_ar ?? ''}`}
        onCancel={() => setReviewing(null)}
        onOk={() => void submit()}
        okText="تأكيد القرار"
        cancelText="إلغاء"
      >
        <Paragraph type="secondary">
          {reviewing?.course_name_ar} — {reviewing?.session_date}
        </Paragraph>
        {approve && (
          <Paragraph>
            القبول سيحوّل سجل الحضور إلى «غياب بعذر» ويُشعر الطالب.
          </Paragraph>
        )}
        <Input.TextArea
          rows={3}
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="ملاحظة تظهر للطالب (اختياري)"
          maxLength={500}
        />
      </Modal>
    </Card>
  );
}
