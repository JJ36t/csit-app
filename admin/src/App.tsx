import { useEffect, useState } from 'react';
import { Avatar, Button, Card, Empty, Layout, Menu, Space, Tag, Typography } from 'antd';
import {
  AuditOutlined,
  CommentOutlined,
  DashboardOutlined,
  LogoutOutlined,
  NotificationOutlined,
  FileProtectOutlined,
  ReadOutlined,
  TableOutlined,
  TeamOutlined,
  TrophyOutlined,
  UserOutlined,
} from '@ant-design/icons';
import LoginPage from './pages/LoginPage';
import StudentsPage from './pages/StudentsPage';
import TimetablePage from './pages/TimetablePage';
import GradesPage from './pages/GradesPage';
import AnnouncementsPage from './pages/AnnouncementsPage';
import UsersPage from './pages/UsersPage';
import AuditPage from './pages/AuditPage';
import DashboardPage from './pages/DashboardPage';
import AcademicPage from './pages/AcademicPage';
import ExcusesPage from './pages/ExcusesPage';
import RequestsPage from './pages/RequestsPage';
import { ApiError, getToken, request, setToken, type AdminUser } from './api';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

const roleLabels: Record<string, string> = {
  college_admin: 'مدير الكلية',
  department_head: 'رئيس قسم',
  instructor: 'تدريسي',
  student: 'طالب',
};

const sectionTitles: Record<string, string> = {
  dashboard: 'لوحة التحكم',
  academic: 'الأكاديمية',
  excuses: 'الأعذار',
  requests: 'طلبات الطلبة',
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

  const canManageAcademic =
    user.role === 'college_admin' || user.role === 'department_head';

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
              { key: 'academic', icon: <ReadOutlined />, label: 'الأكاديمية' },
              { key: 'excuses', icon: <FileProtectOutlined />, label: 'الأعذار' },
              { key: 'requests', icon: <CommentOutlined />, label: 'طلبات الطلبة' },
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

          {active === 'students' && canManageAcademic && <StudentsPage />}
          {active === 'students' && !canManageAcademic && (
            <Card title="الطلاب">
              <Empty description="إدارة الطلاب متاحة لمدير الكلية أو رئيس القسم" />
            </Card>
          )}
          {active === 'timetable' && canManageAcademic && <TimetablePage />}
          {active === 'timetable' && !canManageAcademic && (
            <Card title={sectionTitles.timetable}>
              <Empty description="إدارة الجداول متاحة لمدير الكلية أو رئيس القسم — راجع قسمك لإعادة الضبط" />
            </Card>
          )}
          {active === 'grades' && <GradesPage canPublish={user.role === 'college_admin'} />}
          {active === 'dashboard' && canManageAcademic && <DashboardPage />}
          {active === 'academic' && canManageAcademic && <AcademicPage />}
          {active === 'excuses' && canManageAcademic && <ExcusesPage />}
          {active === 'requests' && canManageAcademic && <RequestsPage />}
          {active === 'announcements' && canManageAcademic && <AnnouncementsPage />}
          {active === 'users' && canManageAcademic && <UsersPage />}
          {active === 'audit' && canManageAcademic && <AuditPage />}
          {active !== 'students' &&
            active !== 'timetable' &&
            active !== 'grades' &&
            active !== 'dashboard' &&
            active !== 'academic' &&
            active !== 'excuses' &&
            active !== 'requests' &&
            active !== 'announcements' &&
            active !== 'users' &&
            active !== 'audit' && (
              <Card title={sectionTitles[active] ?? active}>
                <Empty description="قيد التنفيذ" />
              </Card>
            )}
          {!canManageAcademic &&
            (active === 'dashboard' ||
              active === 'announcements' ||
              active === 'users' ||
              active === 'audit' ||
              active === 'academic' ||
              active === 'excuses' ||
              active === 'requests') && (
              <Card title={sectionTitles[active] ?? active}>
                <Empty description="هذه الشاشة متاحة لمدير الكلية أو رئيس القسم" />
              </Card>
            )}
        </Content>
      </Layout>
    </Layout>
  );
}
