import { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  message,
} from 'antd';
import { DownloadOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import {
  ApiError,
  createGroup,
  createOffering,
  downloadAttendanceReport,
  downloadGradesReport,
  listAdminOfferings,
  listAdminUsers,
  listCourses,
  listDepartments,
  listGroups,
  listTerms,
  type AdminGroup,
  type AdminOffering,
  type AdminUserRow,
  type CourseInfo,
  type Department,
  type TermInfo,
} from '../api';

const { Text } = Typography;

const studyLabels: Record<string, string> = { morning: 'صباحي', evening: 'مسائي' };
const kindLabels: Record<string, string> = { theory: 'نظري', lab: 'مختبر' };

/// الشعب وعروض المواد وتقارير CSV — النقاط التي كانت تُدار بالسكربتات فقط.
export default function AcademicPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [terms, setTerms] = useState<TermInfo[]>([]);
  const [groups, setGroups] = useState<AdminGroup[]>([]);
  const [offerings, setOfferings] = useState<AdminOffering[]>([]);
  const [courses, setCourses] = useState<CourseInfo[]>([]);
  const [instructors, setInstructors] = useState<AdminUserRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [groupForm] = Form.useForm();
  const [offeringForm] = Form.useForm();

  const currentTerm = useMemo(
    () => terms.find((term) => term.is_current) ?? terms[0],
    [terms],
  );

  const loadAll = async (): Promise<void> => {
    setLoading(true);
    try {
      const [deptRes, termRes, groupRes, offeringRes, courseRes, userRes] = await Promise.all([
        listDepartments(),
        listTerms(),
        listGroups(),
        listAdminOfferings(),
        listCourses(),
        listAdminUsers({ role: 'instructor', limit: 200 }),
      ]);
      setDepartments(deptRes);
      setTerms(termRes.items);
      setGroups(groupRes.items);
      setOfferings(offeringRes.items);
      setCourses(courseRes.items);
      setInstructors(userRes.items);
    } catch (error) {
      if (error instanceof ApiError) message.error(error.message);
      else message.error('تعذّر تحميل البيانات الأكاديمية');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submitGroup = async (values: {
    department_id: string;
    stage: number;
    name: string;
    study_type: string;
  }): Promise<void> => {
    if (!currentTerm) {
      message.error('لا يوجد فصل دراسي؛ أنشئ فصلاً أولاً');
      return;
    }
    try {
      await createGroup({ ...values, term_id: currentTerm.term_id });
      message.success('أُنشئت الشعبة');
      groupForm.resetFields(['name']);
      await loadAll();
    } catch (error) {
      if (error instanceof ApiError) message.error(error.message);
    }
  };

  const submitOffering = async (values: {
    course_id: string;
    group_id: string;
    instructor_id?: string;
    session_kind?: string;
  }): Promise<void> => {
    try {
      const created = await createOffering(values);
      message.success(`أُنشئ العرض وسُجّل ${created.enrolled} طالباً تلقائياً`);
      offeringForm.resetFields(['course_id']);
      await loadAll();
    } catch (error) {
      if (error instanceof ApiError) message.error(error.message);
    }
  };

  const report = async (
    offering: AdminOffering,
    kind: 'attendance' | 'grades',
  ): Promise<void> => {
    try {
      if (kind === 'attendance') {
        await downloadAttendanceReport(offering.offering_id, offering.course_code);
      } else {
        await downloadGradesReport(offering.offering_id, offering.course_code);
      }
    } catch (error) {
      if (error instanceof ApiError) message.error(error.message);
      else message.error('تعذّر تنزيل التقرير');
    }
  };

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card
        size="small"
        title="الفصل الدراسي الحالي"
        extra={
          <Button icon={<ReloadOutlined />} onClick={() => void loadAll()} loading={loading}>
            تحديث
          </Button>
        }
      >
        <Text>
          {currentTerm
            ? `${currentTerm.name} — ${currentTerm.year_label} (${currentTerm.start_date ?? ''} → ${currentTerm.end_date ?? ''})`
            : 'لا يوجد فصل دراسي'}
        </Text>
      </Card>

      <Tabs
        items={[
          {
            key: 'groups',
            label: 'الشعب',
            children: (
              <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <Card size="small" title="شعبة جديدة">
                  <Form
                    form={groupForm}
                    layout="inline"
                    onFinish={(values) => void submitGroup(values)}
                    initialValues={{ stage: 1, study_type: 'morning' }}
                  >
                    <Form.Item
                      name="department_id"
                      label="القسم"
                      rules={[{ required: true, message: 'اختر القسم' }]}
                    >
                      <Select
                        style={{ width: 200 }}
                        options={departments.map((dept) => ({
                          value: dept.id,
                          label: dept.name_ar,
                        }))}
                      />
                    </Form.Item>
                    <Form.Item name="stage" label="المرحلة" rules={[{ required: true }]}>
                      <InputNumber min={1} max={8} />
                    </Form.Item>
                    <Form.Item name="name" label="الشعبة" rules={[{ required: true }]}>
                      <Input placeholder="A" style={{ width: 90 }} maxLength={50} />
                    </Form.Item>
                    <Form.Item name="study_type" label="الدراسة">
                      <Select
                        style={{ width: 130 }}
                        options={[
                          { value: 'morning', label: 'صباحي' },
                          { value: 'evening', label: 'مسائي' },
                        ]}
                      />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
                        إنشاء
                      </Button>
                    </Form.Item>
                  </Form>
                </Card>
                <Card size="small" title="الشعب المسجَّلة">
                  <Table<AdminGroup>
                    rowKey="group_id"
                    size="small"
                    loading={loading}
                    dataSource={groups}
                    pagination={{ pageSize: 12, hideOnSinglePage: true }}
                    columns={[
                      { title: 'القسم', dataIndex: 'department_name_ar' },
                      { title: 'المرحلة', dataIndex: 'stage', width: 90 },
                      { title: 'الشعبة', dataIndex: 'name', width: 90 },
                      {
                        title: 'الدراسة',
                        dataIndex: 'study_type',
                        width: 100,
                        render: (value: string) => studyLabels[value] ?? value,
                      },
                      { title: 'الفصل', dataIndex: 'term_name' },
                    ]}
                  />
                </Card>
              </Space>
            ),
          },
          {
            key: 'offerings',
            label: 'عروض المواد',
            children: (
              <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <Card size="small" title="عرض مادة جديد (يسجّل طلبة الشعبة تلقائياً)">
                  <Form
                    form={offeringForm}
                    layout="inline"
                    onFinish={(values) => void submitOffering(values)}
                  >
                    <Form.Item
                      name="group_id"
                      label="الشعبة"
                      rules={[{ required: true, message: 'اختر الشعبة' }]}
                    >
                      <Select
                        style={{ width: 220 }}
                        showSearch
                        optionFilterProp="label"
                        options={groups.map((group) => ({
                          value: group.group_id,
                          label: `${group.department_code} — ${group.stage}${group.name} (${studyLabels[group.study_type] ?? group.study_type})`,
                        }))}
                      />
                    </Form.Item>
                    <Form.Item
                      name="course_id"
                      label="المادة"
                      rules={[{ required: true, message: 'اختر المادة' }]}
                    >
                      <Select
                        style={{ width: 280 }}
                        showSearch
                        optionFilterProp="label"
                        options={courses.map((course) => ({
                          value: course.course_id,
                          label: `${course.code} — ${course.name_ar} (م${course.stage})`,
                        }))}
                      />
                    </Form.Item>
                    <Form.Item name="instructor_id" label="التدريسي">
                      <Select
                        allowClear
                        showSearch
                        optionFilterProp="label"
                        style={{ width: 220 }}
                        options={instructors.map((user) => ({
                          value: user.user_id,
                          label: `${user.full_name_ar} (${user.university_id})`,
                        }))}
                      />
                    </Form.Item>
                    <Form.Item name="session_kind" label="النوع">
                      <Select
                        allowClear
                        style={{ width: 110 }}
                        options={[
                          { value: 'theory', label: 'نظري' },
                          { value: 'lab', label: 'مختبر' },
                        ]}
                      />
                    </Form.Item>
                    <Form.Item>
                      <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
                        إنشاء
                      </Button>
                    </Form.Item>
                  </Form>
                </Card>
                <Card size="small" title="العروض الحالية وتقاريرها">
                  <Table<AdminOffering>
                    rowKey="offering_id"
                    size="small"
                    loading={loading}
                    dataSource={offerings}
                    pagination={{ pageSize: 12, hideOnSinglePage: true }}
                    columns={[
                      {
                        title: 'المادة',
                        render: (_, row) => `${row.course_code} — ${row.course_name_ar}`,
                      },
                      { title: 'الشعبة', width: 110, render: (_, row) => `${row.stage}${row.group_name}` },
                      {
                        title: 'النوع',
                        dataIndex: 'kind',
                        width: 90,
                        render: (value: string) => kindLabels[value] ?? value,
                      },
                      { title: 'التدريسي', dataIndex: 'instructor_name_ar' },
                      {
                        title: 'الطلبة',
                        dataIndex: 'enrolled',
                        width: 80,
                        render: (value: number) => <Tag color="blue">{value}</Tag>,
                      },
                      {
                        title: 'تقارير',
                        width: 230,
                        render: (_, row) => (
                          <Space size={4}>
                            <Button
                              size="small"
                              icon={<DownloadOutlined />}
                              onClick={() => void report(row, 'attendance')}
                            >
                              حضور
                            </Button>
                            <Button
                              size="small"
                              icon={<DownloadOutlined />}
                              onClick={() => void report(row, 'grades')}
                            >
                              درجات
                            </Button>
                          </Space>
                        ),
                      },
                    ]}
                  />
                </Card>
              </Space>
            ),
          },
        ]}
      />
    </Space>
  );
}
