import { useState } from 'react';
import { Alert, Button, Card, Form, Input, Typography } from 'antd';
import { LockOutlined, UserOutlined } from '@ant-design/icons';
import { ApiError, login, setToken, type AdminUser } from '../api';

const { Title, Text } = Typography;

interface Props {
  onLoggedIn: (user: AdminUser) => void;
}

interface FormValues {
  university_id: string;
  password: string;
}

export default function LoginPage({ onLoggedIn }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onFinish = async (values: FormValues): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const res = await login(values.university_id.trim(), values.password);
      setToken(res.access_token);
      onLoggedIn(res.user);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'تعذّر الاتصال بالخادم؛ تأكد أن الخدمة تعمل');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f4f9',
        padding: 24,
      }}
    >
      <Card style={{ width: 420, maxWidth: '100%' }}>
        <Title level={3} style={{ marginBottom: 4 }}>
          لوحة التحكم
        </Title>
        <Text type="secondary">كلية علوم الحاسوب وتكنولوجيا المعلومات — جامعة القادسية</Text>

        {error && <Alert style={{ marginTop: 16 }} type="error" message={error} showIcon />}

        <Form<FormValues> layout="vertical" style={{ marginTop: 24 }} onFinish={onFinish}>
          <Form.Item
            name="university_id"
            label="الرقم الجامعي / اسم المستخدم"
            rules={[{ required: true, message: 'أدخل الرقم الجامعي' }]}
          >
            <Input prefix={<UserOutlined />} autoComplete="username" size="large" />
          </Form.Item>
          <Form.Item
            name="password"
            label="كلمة المرور"
            rules={[{ required: true, message: 'أدخل كلمة المرور' }]}
          >
            <Input.Password prefix={<LockOutlined />} autoComplete="current-password" size="large" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block size="large" loading={loading}>
            دخول
          </Button>
        </Form>
      </Card>
    </div>
  );
}
