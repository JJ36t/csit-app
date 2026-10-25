import { useEffect, useState } from 'react';
import { Avatar, Button, Card, Empty, Layout, Menu, Space, Tag, Typography } from 'antd';
import {
  AuditOutlined,
  DashboardOutlined,
  LogoutOutlined,
  NotificationOutlined,
  TableOutlined,
  TeamOutlined,
  TrophyOutlined,
  UserOutlined,
} from '@ant-design/icons';
import LoginPage from './pages/LoginPage';
import StudentsPage from './pages/StudentsPage';
import { ApiError, getToken, request, setToken, type AdminUser } from './api';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

const roleLabels: Record<string, string> = {
  college_admin: 'مدير الكلية',
  department_head: 'رئيس قسم',
  instructor: 'تدريسي',
  student: 'طالب',
};

const placeholders: Record<string, string> = {
  dashboard: 'ملخص الأرقام الرئيسية — يُبنى في مرحلة لاحقة.',
  timetable: 'إنشاء الحصص وكشف التعارضات ونشر التغييرات — المرحلة التالية.',
  announcements: 'الإعلانات الموجّهة (كلية/قسم/مرحلة/شعبة/مادة) — المرحلة التالية.',
  grades: 'التقييمات وإدخال الدرجات ونشرها وتصديرها — ضمن الإطلاق الأول.',
  users: 'التدريسيون والصلاحيات وإعادة تعيين كلمات المرور — المرحلة التالية.',
  audit: 'من فعل ماذا ومتى: قبل وبعد كل تعديل — المرحلة التالية.',
};

const sectionTitles: Record<string, string> = {
  dashboard: 'لوحة التحكم',
  timetable: 'الجداول',
  announcements: 'الإعلانات',
  grades: 'الدرجات',
  users: 'المستخدمون',
  audit: 'سجل التدقيق',
};

export default function App() {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [active, setActive] = useState('students');

  useEffect(() => {
    if (!getToken()) {
      setChecking(false);
      return;
    }
    request<AdminUser>('/api/v1/auth/me')
      .then(setUser)
      .catch(() => {
        setToken(null);
        setUser(null);
      })
      .finally(() => setChecking(false));
  }, []);

  if (checking) {
    return (
      <div style={{ padding: 64, textAlign: 'center' }}>
        <Text type="secondary">جارٍ التحقق من الجلسة…</Text>
      </div>
    );
  }

  if (!user) {
    return (
      <LoginPage
        onLoggedIn={(loggedIn) => {
          setUser(loggedIn);
          setActive('students');
        }}
      />
    );
  }

  const logout = async (): Promise<void> => {
    try {
      await request<{ ok: boolean }>('/api/v1/auth/logout', { method: 'POST' });
    } catch (e) {
      // الجلسة قد تكون منتهية أصلاً
      if (!(e instanceof ApiError)) throw e;
    }
    setToken(null);
    setUser(null);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Title level={5} style={{ color: '#fff', margin: 0 }}>
          كلية علوم الحاسوب وتكنولوجيا المعلومات — جامعة القادسية
        </Title>
        <Space style={{ marginInlineStart: 'auto' }}>
          <Avatar icon={<UserOutlined />} />
          <Text style={{ color: 'rgba(255,255,255,0.85)' }}>{user.full_name_ar}</Text>
          <Tag color="blue">{roleLabels[user.role] ?? user.role}</Tag>
          <Button icon={<LogoutOutlined />} size="small" onClick={() => void logout()}>
            خروج
          </Button>
        </Space>
      </Header>

      <Layout>
        <Sider width={220} theme="dark">
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[active]}
            onClick={(info) => setActive(info.key)}
            items={[
              { key: 'students', icon: <TeamOutlined />, label: 'الطلاب' },
              { key: 'dashboard', icon: <DashboardOutlined />, label: 'لوحة التحكم' },
              { key: 'timetable', icon: <TableOutlined />, label: 'الجداول' },
              { key: 'announcements', icon: <NotificationOutlined />, label: 'الإعلانات' },
              { key: 'grades', icon: <TrophyOutlined />, label: 'الدرجات' },
              { key: 'users', icon: <UserOutlined />, label: 'المستخدمون' },
              { key: 'audit', icon: <AuditOutlined />, label: 'سجل التدقيق' },
            ]}
          />
        </Sider>

        <Content style={{ padding: 24 }}>
          {user.must_change_password && (
            <Card size="small" style={{ marginBottom: 16, background: '#fffbe6' }}>
              <Text>
                كلمة المرور الأولية ما زالت مستخدمة — غيّرها من تطبيق الجوال (أو من سكربت الإدارة)
                قبل المتابعة.
              </Text>
            </Card>
          )}

          {active === 'students' ? (
            <StudentsPage />
          ) : (
            <Card title={sectionTitles[active] ?? active}>
              <Empty description={placeholders[active] ?? 'قيد التنفيذ'} />
            </Card>
          )}
        </Content>
      </Layout>
    </Layout>
  );
}
