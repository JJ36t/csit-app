import { useCallback, useEffect, useState, type CSSProperties } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Input,
  Row,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { ApiError, listAudit, type AuditRow } from '../api';

const { RangePicker } = DatePicker;
const { Paragraph, Text } = Typography;

/** الوقت يُعرض بتوقيت بغداد — الخادم يخزّن UTC (أرقام لاتينية كبقية الشاشات). */
const baghdadDateTime = (iso: string | null): string => {
  if (!iso) return '—';
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Baghdad',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(new Date(iso));
};

const prettyJson = (value: unknown): string =>
  value === null || value === undefined ? '—' : JSON.stringify(value, null, 2);

const jsonStyle: CSSProperties = {
  margin: 0,
  padding: 8,
  maxHeight: 260,
  overflow: 'auto',
  background: '#fafafa',
  border: '1px solid #f0f0f0',
  borderRadius: 6,
  fontSize: 12,
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
};

interface Filters {
  q: string;
  action: string;
  entity: string;
  actor: string;
  from?: string;
  to?: string;
}

const EMPTY_FILTERS: Filters = { q: '', action: '', entity: '', actor: '' };

export default function AuditPage() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(50);
  const [loading, setLoading] = useState(false);
  const [forbidden, setForbidden] = useState(false);

  const [draft, setDraft] = useState<Filters>(EMPTY_FILTERS);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const res = await listAudit({
        q: filters.q || undefined,
        action: filters.action || undefined,
        entity: filters.entity || undefined,
        actor: filters.actor || undefined,
        date_from: filters.from,
        date_to: filters.to,
        page,
        limit,
      });
      setRows(res.items);
      setTotal(res.total);
      setForbidden(false);
    } catch (e) {
      if (e instanceof ApiError && e.status === 403) {
        setForbidden(true);
        setRows([]);
        setTotal(0);
        return;
      }
      message.error(e instanceof ApiError ? e.message : 'تعذّر تحميل سجل التدقيق');
    } finally {
      setLoading(false);
    }
  }, [filters, page, limit]);

  useEffect(() => {
    void load();
  }, [load]);

  const apply = (): void => {
    setFilters(draft);
    setPage(1);
  };

  const reset = (): void => {
    setDraft(EMPTY_FILTERS);
    setFilters(EMPTY_FILTERS);
    setPage(1);
  };

  if (forbidden) {
    return (
      <Card title="سجل التدقيق">
        <Alert
          type="warning"
          showIcon
          message="لا تملك صلاحية عرض سجل التدقيق"
          description="سجل التدقيق متاح لمدير الكلية فقط، لأنه يضم نشاط جميع المستخدمين. راجع مدير الكلية إن كنت تحتاج إلى معلومة منه."
        />
      </Card>
    );
  }

  const columns = [
    {
      title: 'الوقت (بغداد)',
      dataIndex: 'created_at',
      width: 190,
      render: (value: string | null) => baghdadDateTime(value),
    },
    {
      title: 'الفاعل',
      key: 'actor',
      width: 200,
      render: (_: unknown, row: AuditRow) =>
        row.actor_university_id ? (
          <Space direction="vertical" size={0}>
            <Text>{row.actor_name_ar ?? '—'}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {row.actor_university_id}
            </Text>
          </Space>
        ) : (
          <Text type="secondary">— (نظام)</Text>
        ),
    },
    {
      title: 'الإجراء',
      dataIndex: 'action',
      width: 170,
      render: (value: string) => <Tag color="blue">{value}</Tag>,
    },
    {
      title: 'الكيان',
      key: 'entity',
      width: 190,
      render: (_: unknown, row: AuditRow) => (
        <Space direction="vertical" size={0}>
          <Text>{row.entity}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {row.entity_id}
          </Text>
        </Space>
      ),
    },
    { title: 'العنوان', dataIndex: 'ip', width: 130, render: (value: string | null) => value ?? '—' },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card title="سجل التدقيق">
        <Row gutter={[12, 12]}>
          <Col xs={24} md={8}>
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder="بحث في رقم الكيان أو الإجراء"
              value={draft.q}
              onChange={(e) => setDraft({ ...draft, q: e.target.value })}
              onPressEnter={apply}
            />
          </Col>
          <Col xs={12} md={4}>
            <Input
              allowClear
              placeholder="الإجراء (action)"
              value={draft.action}
              onChange={(e) => setDraft({ ...draft, action: e.target.value })}
              onPressEnter={apply}
            />
          </Col>
          <Col xs={12} md={4}>
            <Input
              allowClear
              placeholder="الكيان (entity)"
              value={draft.entity}
              onChange={(e) => setDraft({ ...draft, entity: e.target.value })}
              onPressEnter={apply}
            />
          </Col>
          <Col xs={12} md={4}>
            <Input
              allowClear
              placeholder="الرقم الجامعي للفاعل"
              value={draft.actor}
              onChange={(e) => setDraft({ ...draft, actor: e.target.value })}
              onPressEnter={apply}
            />
          </Col>
          <Col xs={12} md={4}>
            <RangePicker
              format="YYYY-MM-DD"
              style={{ width: '100%' }}
              value={draft.from && draft.to ? [dayjs(draft.from), dayjs(draft.to)] : null}
              onChange={(value) =>
                setDraft({
                  ...draft,
                  from: value?.[0]?.format('YYYY-MM-DD'),
                  to: value?.[1]?.format('YYYY-MM-DD'),
                })
              }
            />
          </Col>
          <Col xs={24} md={24}>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={apply}>
                تطبيق المرشحات
              </Button>
              <Button onClick={reset}>مسح</Button>
              <Button icon={<ReloadOutlined />} loading={loading} onClick={() => void load()}>
                تحديث
              </Button>
              <Text type="secondary">الأوقات بتوقيت بغداد، والسجلات مرتبة بالأحدث.</Text>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <Table<AuditRow>
          rowKey="audit_id"
          loading={loading}
          dataSource={rows}
          columns={columns}
          scroll={{ x: 900 }}
          pagination={{
            current: page,
            pageSize: limit,
            total,
            showSizeChanger: true,
            pageSizeOptions: [20, 50, 100, 200],
            showTotal: (count) => `إجمالي ${count} سجلاً`,
            onChange: (nextPage, nextSize) => {
              if (nextSize !== limit) {
                setLimit(nextSize);
                setPage(1);
                return;
              }
              setPage(nextPage);
            },
          }}
          expandable={{
            expandedRowRender: (row) => (
              <Row gutter={[12, 12]}>
                <Col xs={24} md={12}>
                  <Paragraph strong style={{ marginBottom: 4 }}>
                    قبل
                  </Paragraph>
                  <pre dir="ltr" style={{ ...jsonStyle, textAlign: 'left' }}>
                    {prettyJson(row.before)}
                  </pre>
                </Col>
                <Col xs={24} md={12}>
                  <Paragraph strong style={{ marginBottom: 4 }}>
                    بعد
                  </Paragraph>
                  <pre dir="ltr" style={{ ...jsonStyle, textAlign: 'left' }}>
                    {prettyJson(row.after)}
                  </pre>
                </Col>
              </Row>
            ),
          }}
        />
      </Card>
    </Space>
  );
}
