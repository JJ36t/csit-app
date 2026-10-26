import { useCallback, useEffect, useState, type ReactNode } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Progress,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd';
import {
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  NotificationOutlined,
  ReloadOutlined,
  TeamOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { ApiError, getOverview, type OverviewData } from '../api';

const { Text } = Typography;

type DepartmentRow = OverviewData['students']['by_department'][number];

interface StatCard {
  key: string;
  title: string;
  value: number;
  hint: string;
  icon: ReactNode;
  color?: string;
}

export default function DashboardPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      setData(await getOverview());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'تعذّر تحميل أرقام لوحة التحكم');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const today = data?.today;
  const grades = data?.grades;
  const announcements = data?.announcements;
  const departments = data?.students.by_department ?? [];
  const total = data?.students.total ?? 0;
  const populated = departments.filter((row) => row.count > 0).length;

  const cards: StatCard[] = [
    {
      key: 'students',
      title: 'الطلاب',
      value: total,
      hint: `${populated} قسم فيه طلاب`,
      icon: <TeamOutlined />,
    },
    {
      key: 'sessions',
      title: 'جلسات اليوم',
      value: today?.sessions ?? 0,
      hint: 'بتوقيت بغداد',
      icon: <CalendarOutlined />,
    },
    {
      key: 'present',
      title: 'حاضر اليوم',
      value: today?.present ?? 0,
      hint: `متأخر: ${today?.late ?? 0}`,
      icon: <CheckCircleOutlined />,
      color: '#237804',
    },
    {
      key: 'absent',
      title: 'غائب اليوم',
      value: today?.absent ?? 0,
      hint: `من ${today?.sessions ?? 0} جلسة`,
      icon: <CloseCircleOutlined />,
      color: '#a8071a',
    },
    {
      key: 'published',
      title: 'تقييمات منشورة',
      value: grades?.published ?? 0,
      hint: `مسودات: ${grades?.drafts ?? 0}`,
      icon: <TrophyOutlined />,
      color: '#1f4e79',
    },
    {
      key: 'announcements',
      title: 'إعلانات نشطة',
      value: announcements?.active ?? 0,
      hint: `مجدولة: ${announcements?.scheduled ?? 0}`,
      icon: <NotificationOutlined />,
    },
  ];

  const columns = [
    {
      title: 'القسم',
      dataIndex: 'name_ar',
      key: 'department',
      render: (name: string, row: DepartmentRow) => (
        <Space size={6}>
          <Text strong>{name}</Text>
          <Tag>{row.code}</Tag>
        </Space>
      ),
    },
    {
      title: 'عدد الطلاب',
      dataIndex: 'count',
      key: 'count',
      width: 130,
      render: (count: number) => <Text strong>{count}</Text>,
    },
    {
      title: 'النسبة',
      dataIndex: 'count',
      key: 'share',
      width: 220,
      render: (count: number) => (
        <Progress
          size="small"
          percent={total > 0 ? Math.round((count / total) * 100) : 0}
          strokeColor="#1f4e79"
        />
      ),
    },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card
        title="لوحة التحكم"
        extra={
          <Button
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={() => {
              void load();
            }}
          >
            تحديث
          </Button>
        }
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          {error && (
            <Alert
              type="error"
              showIcon
              message="تعذّر تحميل أرقام اللوحة"
              description={error}
              action={
                <Button
                  size="small"
                  onClick={() => {
                    void load();
                  }}
                >
                  إعادة المحاولة
                </Button>
              }
            />
          )}

          <Row gutter={[16, 16]}>
            {cards.map((card) => (
              <Col key={card.key} xs={24} sm={12} md={8} xl={4}>
                <Card size="small" loading={loading && !data}>
                  <Statistic
                    title={
                      <Space size={6}>
                        {card.icon}
                        <span>{card.title}</span>
                      </Space>
                    }
                    value={card.value}
                    valueStyle={card.color ? { color: card.color } : undefined}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {card.hint}
                  </Text>
                </Card>
              </Col>
            ))}
          </Row>
        </Space>
      </Card>

      <Card
        title="توزيع الطلاب على الأقسام"
        extra={<Text type="secondary">الإجمالي: {total} طالب</Text>}
      >
        <Table<DepartmentRow>
          size="middle"
          rowKey="code"
          loading={loading}
          dataSource={departments}
          columns={columns}
          pagination={false}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="لا توجد أقسام لعرضها"
              />
            ),
          }}
        />
        <Text type="secondary" style={{ fontSize: 12, display: 'inline-block', marginTop: 12 }}>
          <ClockCircleOutlined /> الحضور والجلسات محسوبة على تاريخ اليوم بتوقيت بغداد، والتقييمات
          والإعلانات ضمن نطاقك فقط.
        </Text>
      </Card>
    </Space>
  );
}
