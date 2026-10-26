import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Divider,
  Empty,
  Form,
  Input,
  InputNumber,
  Row,
  Select,
  Space,
  Table,
  Tag,
  TimePicker,
  Typography,
  message,
} from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs, { type Dayjs } from 'dayjs';
import {
  ApiError,
  createChange,
  createRoom,
  createSlot,
  listOfferings,
  listRooms,
  listSlots,
  listTimetable,
  listTimetableChanges,
  type Offering,
  type Room,
  type TimetableChangeRow,
  type TimetableSession,
  type WeeklySlot,
} from '../api';

const { Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;

const WEEKDAYS = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
const studyLabel: Record<string, string> = { morning: 'صباحي', evening: 'مسائي' };
const kindLabel: Record<string, string> = { theory: 'نظري', lab: 'مختبر' };
const statusLabel: Record<string, string> = {
  scheduled: 'مجدولة',
  open: 'مفتوحة',
  closed: 'مغلقة',
  cancelled: 'ملغاة',
};
const statusColor: Record<string, string> = {
  scheduled: 'blue',
  open: 'green',
  closed: 'default',
  cancelled: 'red',
};
const changeLabel: Record<string, string> = {
  cancel: 'إلغاء',
  move: 'نقل',
  extra: 'إضافة',
};
const changeColor: Record<string, string> = { cancel: 'red', move: 'orange', extra: 'green' };

/** توقيت بغداد للعرض فقط — التخزين في الخادم UTC. */
const baghdadTime = (iso: string): string =>
  new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Baghdad',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(iso));

interface SlotFormValues {
  offering_id: string;
  weekday: number;
  start_time: Dayjs;
  end_time: Dayjs;
  room_id?: string;
  kind: string;
}

interface RoomFormValues {
  name: string;
  building?: string;
  lat?: number;
  lng?: number;
  radius_m?: number;
}

interface ChangeFormValues {
  slot_id: string;
  date: Dayjs;
  type: string;
  new_start?: Dayjs;
  reason?: string;
}

interface Notice {
  kind: 'success' | 'error' | 'info';
  text: string;
  hint?: string;
}

function failureText(error: unknown, fallback: string): Notice {
  if (error instanceof ApiError) {
    const details = error.details ? JSON.stringify(error.details) : '';
    return {
      kind: 'error',
      text: error.message,
      hint: `${error.code}${details ? ` · ${details}` : ''}`,
    };
  }
  return { kind: 'error', text: fallback };
}

export default function TimetablePage() {
  const [offerings, setOfferings] = useState<Offering[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [slots, setSlots] = useState<WeeklySlot[]>([]);
  const [sessions, setSessions] = useState<TimetableSession[]>([]);
  const [changes, setChanges] = useState<TimetableChangeRow[]>([]);
  const [range, setRange] = useState<[Dayjs, Dayjs]>([dayjs(), dayjs().add(13, 'day')]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);

  const [slotForm] = Form.useForm<SlotFormValues>();
  const [roomForm] = Form.useForm<RoomFormValues>();
  const [changeForm] = Form.useForm<ChangeFormValues>();
  const changeType = Form.useWatch('type', changeForm);

  const from = range[0].format('YYYY-MM-DD');
  const to = range[1].format('YYYY-MM-DD');

  const load = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const [roomRes, slotRes, sessionRes, changeRes] = await Promise.all([
        listRooms(),
        listSlots(),
        listTimetable(from, to),
        listTimetableChanges(from, to),
      ]);
      setRooms(roomRes.items);
      setSlots(slotRes.items);
      setSessions(sessionRes.items);
      setChanges(changeRes.items);
    } catch (error) {
      setNotice(failureText(error, 'تعذّر تحميل بيانات الجدول'));
    } finally {
      setLoading(false);
    }
  }, [from, to]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    listOfferings()
      .then((res) => setOfferings(res.items))
      .catch(() => message.error('تعذّر تحميل قائمة المواد'));
  }, []);

  const submitRoom = async (values: RoomFormValues): Promise<void> => {
    setSaving(true);
    setNotice(null);
    try {
      const created = await createRoom({
        name: values.name.trim(),
        building: values.building?.trim() || null,
        lat: values.lat ?? null,
        lng: values.lng ?? null,
        radius_m: values.radius_m ?? null,
      });
      setNotice({ kind: 'success', text: `أُضيفت القاعة «${created.name}»` });
      roomForm.resetFields();
      await load();
    } catch (error) {
      setNotice(failureText(error, 'تعذّر إنشاء القاعة'));
    } finally {
      setSaving(false);
    }
  };

  const submitSlot = async (values: SlotFormValues): Promise<void> => {
    setSaving(true);
    setNotice(null);
    try {
      const created = await createSlot({
        offering_id: values.offering_id,
        weekday: values.weekday,
        start_time: values.start_time.format('HH:mm:ss'),
        end_time: values.end_time.format('HH:mm:ss'),
        room_id: values.room_id ?? null,
        kind: values.kind,
      });
      setNotice({
        kind: 'success',
        text: `أُضيفت الحصة الأسبوعية ووُلّدت ${created.sessions_created} جلسة`,
      });
      slotForm.resetFields(['offering_id', 'start_time', 'end_time', 'room_id', 'kind']);
      await load();
    } catch (error) {
      setNotice(failureText(error, 'تعذّر إنشاء الحصة'));
    } finally {
      setSaving(false);
    }
  };

  const submitChange = async (values: ChangeFormValues): Promise<void> => {
    setSaving(true);
    setNotice(null);
    try {
      const created = await createChange({
        slot_id: values.slot_id,
        date: values.date.format('YYYY-MM-DD'),
        type: values.type,
        new_start:
          values.type === 'cancel' ? null : values.new_start?.format('HH:mm:ss') ?? null,
        reason: values.reason?.trim() || null,
      });
      setNotice({
        kind: 'success',
        text: `سُجّل التغيير (${changeLabel[created.type] ?? created.type}) وأُشعر الطلاب عبر الجدول`,
      });
      changeForm.resetFields(['date', 'new_start', 'reason']);
      await load();
    } catch (error) {
      setNotice(failureText(error, 'تعذّر تسجيل التغيير'));
    } finally {
      setSaving(false);
    }
  };

  const slotColumns = [
    {
      title: 'اليوم',
      dataIndex: 'weekday',
      width: 90,
      render: (value: number) => WEEKDAYS[value] ?? value,
    },
    {
      title: 'الوقت',
      key: 'time',
      width: 130,
      render: (_: unknown, row: WeeklySlot) => `${row.start_time.slice(0, 5)} – ${row.end_time.slice(0, 5)}`,
    },
    {
      title: 'المادة',
      key: 'course',
      render: (_: unknown, row: WeeklySlot) => (
        <Space direction="vertical" size={0}>
          <Text strong>{row.course_name_ar}</Text>
          <Text type="secondary">
            {row.course_code} · المرحلة {row.stage} · شعبة {row.group_name} ·{' '}
            {studyLabel[row.study_type] ?? row.study_type}
          </Text>
        </Space>
      ),
    },
    {
      title: 'القاعة',
      dataIndex: 'room_name',
      width: 120,
      render: (value: string | null) => value ?? '—',
    },
    {
      title: 'التدريسي',
      dataIndex: 'instructor_name_ar',
      width: 160,
      render: (value: string | null) => value ?? '—',
    },
    {
      title: 'النوع',
      dataIndex: 'kind',
      width: 90,
      render: (value: string) => <Tag>{kindLabel[value] ?? value}</Tag>,
    },
  ];

  const sessionColumns = [
    { title: 'التاريخ', dataIndex: 'date', width: 110 },
    {
      title: 'الوقت',
      key: 'time',
      width: 120,
      render: (_: unknown, row: TimetableSession) =>
        `${baghdadTime(row.starts_at)} – ${baghdadTime(row.ends_at)}`,
    },
    {
      title: 'المادة',
      key: 'course',
      render: (_: unknown, row: TimetableSession) => (
        <Space direction="vertical" size={0}>
          <Text strong>{row.course_name_ar}</Text>
          <Text type="secondary">{row.course_code}</Text>
        </Space>
      ),
    },
    {
      title: 'القاعة',
      dataIndex: 'room',
      width: 110,
      render: (value: string | null) => value ?? '—',
    },
    {
      title: 'الحالة',
      dataIndex: 'status',
      width: 100,
      render: (value: string) => (
        <Tag color={statusColor[value] ?? 'default'}>{statusLabel[value] ?? value}</Tag>
      ),
    },
  ];

  const changeColumns = [
    { title: 'التاريخ', dataIndex: 'date', width: 110 },
    {
      title: 'النوع',
      dataIndex: 'type',
      width: 90,
      render: (value: string) => (
        <Tag color={changeColor[value] ?? 'default'}>{changeLabel[value] ?? value}</Tag>
      ),
    },
    { title: 'المادة', dataIndex: 'course_name_ar' },
    {
      title: 'وقت جديد',
      dataIndex: 'new_start',
      width: 100,
      render: (value: string | null) => (value ? value.slice(0, 5) : '—'),
    },
    {
      title: 'السبب',
      dataIndex: 'reason',
      render: (value: string | null) => value ?? '—',
    },
  ];

  const offeringOptions = offerings.map((item) => ({
    value: item.offering_id,
    label: `${item.course_code} — ${item.course_name_ar} (${item.group_name} · المرحلة ${item.stage})`,
  }));

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
        title="الحصص في نطاق زمني"
        extra={
          <Space>
            <RangePicker
              value={range}
              format="YYYY-MM-DD"
              allowClear={false}
              onChange={(value) => {
                if (value && value[0] && value[1]) setRange([value[0], value[1]]);
              }}
            />
            <Button icon={<ReloadOutlined />} onClick={() => void load()} loading={loading}>
              تحديث
            </Button>
          </Space>
        }
      >
        <Table<TimetableSession>
          size="small"
          rowKey="session_id"
          loading={loading}
          dataSource={sessions}
          columns={sessionColumns}
          pagination={{ pageSize: 10, hideOnSinglePage: true }}
          locale={{ emptyText: 'لا حصص في هذا النطاق — أنشئ حصة أسبوعية أو وسّع النطاق' }}
        />
      </Card>

      <Card title="التغييرات المؤرخة في النطاق">
        <Table<TimetableChangeRow>
          size="small"
          rowKey="change_id"
          loading={loading}
          dataSource={changes}
          columns={changeColumns}
          pagination={{ pageSize: 8, hideOnSinglePage: true }}
          locale={{ emptyText: 'لا تغييرات مسجّلة في هذا النطاق' }}
        />
      </Card>

      <Card title="الخطة الأسبوعية الثابتة">
        <Table<WeeklySlot>
          size="small"
          rowKey="slot_id"
          loading={loading}
          dataSource={slots}
          columns={slotColumns}
          pagination={false}
          locale={{ emptyText: 'لا حصص أسبوعية بعد — أضف حصة من النموذج أدناه' }}
        />
      </Card>

      <Row gutter={16}>
        <Col xs={24} xl={12}>
          <Card title="إضافة حصة أسبوعية">
            <Paragraph type="secondary" style={{ marginTop: 0 }}>
              تُولَّد جلسات الفصل تلقائياً عند إنشاء الحصة، ويرفض الخادم أي تداخل في القاعة أو
              التدريسي أو الشعبة برسالة عربية.
            </Paragraph>
            <Form<SlotFormValues>
              form={slotForm}
              layout="vertical"
              onFinish={(values) => void submitSlot(values)}
              initialValues={{ kind: 'theory', weekday: 0 }}
            >
              <Form.Item
                name="offering_id"
                label="المادة"
                rules={[{ required: true, message: 'اختر المادة' }]}
              >
                <Select
                  showSearch
                  optionFilterProp="label"
                  placeholder="اختر مادة من مواد الكلية"
                  options={offeringOptions}
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Row gutter={12}>
                <Col span={8}>
                  <Form.Item
                    name="weekday"
                    label="اليوم"
                    rules={[{ required: true, message: 'اختر اليوم' }]}
                  >
                    <Select
                      style={{ width: '100%' }}
                      options={WEEKDAYS.map((label, value) => ({ value, label }))}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="start_time"
                    label="البداية"
                    rules={[{ required: true, message: 'حدّد وقت البداية' }]}
                  >
                    <TimePicker format="HH:mm" minuteStep={5} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="end_time"
                    label="النهاية"
                    rules={[{ required: true, message: 'حدّد وقت النهاية' }]}
                  >
                    <TimePicker format="HH:mm" minuteStep={5} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={12}>
                <Col span={14}>
                  <Form.Item name="room_id" label="القاعة">
                    <Select
                      style={{ width: '100%' }}
                      allowClear
                      placeholder="بلا قاعة محددة"
                      options={rooms.map((room) => ({
                        value: room.room_id,
                        label: room.building ? `${room.name} — ${room.building}` : room.name,
                      }))}
                    />
                  </Form.Item>
                </Col>
                <Col span={10}>
                  <Form.Item name="kind" label="النوع">
                    <Select
                      style={{ width: '100%' }}
                      options={[
                        { value: 'theory', label: 'نظري' },
                        { value: 'lab', label: 'مختبر' },
                      ]}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Button type="primary" htmlType="submit" icon={<PlusOutlined />} loading={saving}>
                إنشاء الحصة
              </Button>
            </Form>
          </Card>
        </Col>

        <Col xs={24} xl={12}>
          <Card title="تسجيل تغيير مؤرّخ">
            <Paragraph type="secondary" style={{ marginTop: 0 }}>
              الإلغاء يحتاج جلسة قائمة في ذلك التاريخ، والنقل يحتاج وقتاً جديداً. كل تغيير يُسجَّل
              في سجل التدقيق ويُدقَّق ضد تعارضات القاعة والتدريسي والشعبة.
            </Paragraph>
            <Form<ChangeFormValues>
              form={changeForm}
              layout="vertical"
              onFinish={(values) => void submitChange(values)}
              initialValues={{ type: 'cancel' }}
            >
              <Form.Item
                name="slot_id"
                label="الحصة الأسبوعية"
                rules={[{ required: true, message: 'اختر الحصة' }]}
              >
                <Select
                  showSearch
                  optionFilterProp="label"
                  placeholder="اختر حصة من الخطة الأسبوعية"
                  options={slots.map((slot) => ({
                    value: slot.slot_id,
                    label: `${slot.course_code} · ${WEEKDAYS[slot.weekday]} ${slot.start_time.slice(0, 5)} (${slot.group_name})`,
                  }))}
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item
                    name="date"
                    label="التاريخ"
                    rules={[{ required: true, message: 'اختر التاريخ' }]}
                  >
                    <DatePicker format="YYYY-MM-DD" style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="type"
                    label="نوع التغيير"
                    rules={[{ required: true, message: 'اختر النوع' }]}
                  >
                    <Select
                      style={{ width: '100%' }}
                      options={[
                        { value: 'cancel', label: 'إلغاء الحصة' },
                        { value: 'move', label: 'نقل إلى وقت آخر' },
                        { value: 'extra', label: 'حصة إضافية' },
                      ]}
                    />
                  </Form.Item>
                </Col>
              </Row>

              {changeType !== 'cancel' && (
                <Form.Item
                  name="new_start"
                  label="وقت البداية الجديد"
                  rules={[{ required: true, message: 'حدّد الوقت الجديد' }]}
                >
                  <TimePicker format="HH:mm" minuteStep={5} style={{ width: '100%' }} />
                </Form.Item>
              )}

              <Form.Item name="reason" label="السبب">
                <Input placeholder="مثال: عطلة رسمية، اجتماع قسم" maxLength={300} />
              </Form.Item>

              <Button type="primary" htmlType="submit" icon={<PlusOutlined />} loading={saving}>
                تسجيل التغيير
              </Button>
            </Form>
          </Card>
        </Col>
      </Row>

      <Card title="القاعات">
        <Row gutter={16}>
          <Col xs={24} xl={12}>
            {rooms.length === 0 ? (
              <Empty description="لا قاعات مسجّلة — أضف أول قاعة من النموذج المجاور" />
            ) : (
              <Table<Room>
                size="small"
                rowKey="room_id"
                dataSource={rooms}
                pagination={false}
                columns={[
                  { title: 'القاعة', dataIndex: 'name' },
                  {
                    title: 'المبنى',
                    dataIndex: 'building',
                    render: (value: string | null) => value ?? '—',
                  },
                  {
                    title: 'نطاق الموقع',
                    dataIndex: 'radius_m',
                    width: 120,
                    render: (value: number | null) => (value ? `${value} م` : '—'),
                  },
                  {
                    title: 'الإحداثيات',
                    key: 'coords',
                    render: (_: unknown, row: Room) =>
                      row.lat !== null && row.lng !== null
                        ? `${row.lat.toFixed(4)}, ${row.lng.toFixed(4)}`
                        : '—',
                  },
                ]}
              />
            )}
          </Col>
          <Col xs={24} xl={12}>
            <Divider orientation="right" style={{ marginTop: 0 }}>
              قاعة جديدة
            </Divider>
            <Form<RoomFormValues>
              form={roomForm}
              layout="vertical"
              onFinish={(values) => void submitRoom(values)}
            >
              <Row gutter={12}>
                <Col span={14}>
                  <Form.Item
                    name="name"
                    label="اسم القاعة"
                    rules={[
                      { required: true, message: 'أدخل اسم القاعة' },
                      { min: 2, message: 'الاسم قصير جداً' },
                    ]}
                  >
                    <Input placeholder="قاعة 101 أو مختبر الشبكات" maxLength={100} />
                  </Form.Item>
                </Col>
                <Col span={10}>
                  <Form.Item name="building" label="المبنى">
                    <Input placeholder="مبنى أ" maxLength={100} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={12}>
                <Col span={8}>
                  <Form.Item name="lat" label="خط العرض">
                    <InputNumber style={{ width: '100%' }} step={0.0001} placeholder="31.9900" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="lng" label="خط الطول">
                    <InputNumber style={{ width: '100%' }} step={0.0001} placeholder="44.9200" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="radius_m" label="نطاق (متر)">
                    <InputNumber style={{ width: '100%' }} min={10} max={2000} step={10} />
                  </Form.Item>
                </Col>
              </Row>
              <Button type="primary" htmlType="submit" icon={<PlusOutlined />} loading={saving}>
                إضافة القاعة
              </Button>
            </Form>
          </Col>
        </Row>
      </Card>
    </Space>
  );
}
