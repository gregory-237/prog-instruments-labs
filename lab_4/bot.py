import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.filters.state import StatesGroup, State, default_state

from config import BOT_TOKEN
from db_worker import DatabaseWorker
from db_order import DatabaseOrder
from utility import start_places, has_places

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db_worker = DatabaseWorker()
db_order = DatabaseOrder()


class EnterWorkerData(StatesGroup):
    waiting_for_city = State()
    waiting_for_number = State()
    waiting_for_name = State()
    waiting_for_surname = State()


class EnterOrderData(StatesGroup):
    waiting_for_order = State()


@dp.message_handler(CommandStart())
async def cmd_start(message: types.Message):
    if not db_worker.is_registered(message.from_user.id):
        start_reg_markup = types.InlineKeyboardMarkup(resize_keyboard=True, one_time_keybord=True)
        bt1 = types.InlineKeyboardButton('💪Начать регистрацию💪', callback_data='registration')
        start_reg_markup.add(bt1)
        await message.answer(
            f'Привет! Это бот для обработки заказов компании «Халтура».\n\nМы рады тебя приветствовать!'
            f' Надеемся на долгое и плодотворное сотрудничество🤝'
            f'\n\nДля начала нужно пройти регистрацию, воспользуйся кнопкой ниже\n'
            f'👇👇👇👇👇 ', reply_markup=start_reg_markup)
    elif db_worker.is_registered(message.from_user.id) and not db_worker.is_admin(message.from_user.id):
        start_work_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        bt1 = types.KeyboardButton('👤Мои данные')
        bt2 = types.KeyboardButton('🤝Мои заявки')
        start_work_markup.row(bt1, bt2)
        await message.answer('Можем приступить к работе🤝', reply_markup=start_work_markup)
    elif db_worker.is_admin(message.from_user.id):
        start_work_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        bt1 = types.KeyboardButton('⛑Данные рабочих')
        bt2 = types.KeyboardButton('🔖Заказы')
        bt3 = types.KeyboardButton('📩Выложить заказ')
        start_work_markup.row(bt1, bt2)
        start_work_markup.row(bt3)
        await message.answer('✨Привет, ты являешься администратором бота,'
                             ' можешь просматривать данные рабочих и оповещать их о новых заказах.💵'
                             '\n 🔔Также тебе будут приходить оповещения об откликах рабочих.',
                             reply_markup=start_work_markup)


@dp.callback_query_handler(state=default_state, text_startswith='registration')
async def registration(callback: types.CallbackQuery, state: FSMContext):
    if callback.message.chat.type == 'private':
        await callback.message.delete()
        await callback.message.answer('👇Для начала - введи номер телефона для связи👇\n'
                                      '⚠️В формате <code>+79XXXXXXXXX</code>', parse_mode='html')
        await state.set_state(EnterWorkerData.waiting_for_number.state)


@dp.message_handler(state=EnterWorkerData.waiting_for_number)
async def number_chosen(message: types.Message, state: FSMContext):
    reg_city_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    bt1 = types.KeyboardButton("Новокуйбышевск")
    bt2 = types.KeyboardButton("Самара")
    bt3 = types.KeyboardButton("Казань")
    reg_city_markup.row(bt1, bt2, bt3)
    await message.answer('📱')
    await message.answer('👇Теперь выбери свой город👇', reply_markup=reg_city_markup)
    await state.update_data(phone_number=message.text)
    await state.set_state(EnterWorkerData.waiting_for_city.state)


@dp.message_handler(state=EnterWorkerData.waiting_for_city.state)
async def city_chosen(message: types.Message, state: FSMContext):
    await message.answer('🏠')
    await message.answer('👇Теперь введи только фамилию👇')
    await state.update_data(city=message.text)
    await state.set_state(EnterWorkerData.waiting_for_surname.state)


@dp.message_handler(state=EnterWorkerData.waiting_for_surname.state)
async def surname_chosen(message: types.Message, state: FSMContext):
    await message.answer('✏️')
    await message.answer('👇Теперь введи только имя👇')
    await state.update_data(surname=message.text)
    await state.set_state(EnterWorkerData.waiting_for_name.state)


@dp.message_handler(state=EnterWorkerData.waiting_for_name.state)
async def surname_chosen(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('🪪')
    worker_data = await state.get_data()
    start_work_markup = types.InlineKeyboardMarkup(resize_keyboard=True)
    bt1 = types.InlineKeyboardButton('✅Приступить к работе', callback_data='start_work')
    start_work_markup.add(bt1)
    db_worker.add_worker(message.from_user.id, worker_data["phone_number"],
                         f'{worker_data["surname"]} {worker_data["name"]}',
                         worker_data["city"])
    await message.answer(f'👤Твой профиль\n\n📱Телефон: {worker_data["phone_number"]}'
                         f'\n🌍Город: {worker_data["city"]}'
                         f'\n👷🏻‍♂️ФИО: {worker_data["surname"]} {worker_data["name"]}',
                         reply_markup=start_work_markup)
    await state.finish()


@dp.message_handler(commands=['order'], state=default_state)
async def send_order(message: types.Message, state: FSMContext):
    if message.chat.type == 'private':
        await message.answer('📨Отправь данные заказа согласно формату')
        await state.set_state(EnterOrderData.waiting_for_order.state)


@dp.message_handler(content_types=['text'])
async def messages(message: types.Message):
    if message.text == '👤Мои данные':
        worker_data = db_worker.info_worker(message.from_user.id)
        profile_markup = types.InlineKeyboardMarkup(resize_keyboard=True)
        bt1 = types.InlineKeyboardButton('📊Статистика заказов', callback_data='statistics')
        bt2 = types.InlineKeyboardButton('📝Редактировать данные', callback_data='edit')
        profile_markup.row(bt1, bt2)
        await message.answer(f'👤Твой профиль\n\n📱Телефон: {worker_data[1]}'
                             f'\n🌍Город: {worker_data[3]}'
                             f'\n👷🏻‍♂️ФИО: {worker_data[2]}', reply_markup=profile_markup)
    elif message.text == '🤝Мои заявки':
        if db_order.all_orders(message.from_user.id):
            pass
        else:
            await message.answer('❌У вас пока что нет заявок')

    elif message.text == '⛑Данные рабочих':
        pass

    elif message.text == '🔖Заказы':
        pass

    elif message.text == '📩Выложить заказ':
        await message.answer('⚠️Для того, чтобы выложить заказ используй команду /order\n'
                             ' и после нее пропиши данные заказа в формате:\n\n'
                             'Город\n'
                             'Количество человек\n'
                             'Минималка (часов)\n'
                             'Адрес\n'
                             'Время прибытия\n'
                             'Описание заказа\n'
                             'Время работы (часов)\n'
                             'Оплата в час (руб.)\n\n'
                             '📶Пример заказа:\n\n'
                             '<code>Город|</code>Самара\n'
                             '<code>Количество человек|</code>2\n'
                             '<code>Минималка (часов)|</code>2\n'
                             '<code>Адрес|</code>Кафе Рио\n'
                             '<code>Время прибытия|</code>завтра 10:00\n'
                             '<code>Описание заказа|</code>Копать траншею (30см в длину)\n'
                             '<code>Время работы (часов)|</code>3\n'
                             '<code>Оплата в час (руб.)|</code>450\n\n'
                             '💡Лучше скопируй пример и поменяй все пункты, чтобы не ошибиться.', parse_mode='html')


@dp.message_handler(state=EnterOrderData.waiting_for_order.state)
async def confirm_send_order(message: types.Message, state: FSMContext):
    await state.update_data(order_text=message.text)
    order_data = await state.get_data()
    send_order_markup = types.InlineKeyboardMarkup(resize_keyboard=True)
    bt1 = types.InlineKeyboardButton('✅Все верно, разослать заказ', callback_data='send_order')
    send_order_markup.add(bt1)
    await message.answer(f'{order_data["order_text"]}',
                         reply_markup=send_order_markup)
    await state.finish()


@dp.callback_query_handler(text_startswith='statistics')
async def statistics(callback: types.CallbackQuery):
    await callback.message.edit_text(f'📊Статистика заказов:\n\n'
                                     f'🤝Всего заявок: {len(db_order.all_orders(callback.from_user.id))}\n'
                                     f'✅Выполнено: {len(list(filter(lambda order: order[10] == 2, db_order.all_orders(callback.from_user.id))))}\n'
                                     f'⛔️Брак: {len(list(filter(lambda order: order[10] == 3, db_order.all_orders(callback.from_user.id))))}')


@dp.callback_query_handler(text_startswith='start_work')
async def start_work(callback: types.CallbackQuery):
    start_work_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bt1 = types.KeyboardButton('👤Мои данные')
    bt2 = types.KeyboardButton('🤝Мои заявки')
    start_work_markup.row(bt1, bt2)
    await callback.message.delete()
    await callback.message.answer('🗝')
    await callback.message.answer('Поздравляем с успешной регистрацией✅\n'
                                  '⏳Ожидай появления новых заявок!\n'
                                  '🆗Принять заявку можно, нажав на активные кнопки под заявкой.',
                                  reply_markup=start_work_markup)


@dp.callback_query_handler(text_startswith='send_order')
async def send_all_order(callback: types.CallbackQuery):
    order_id = f'{callback.from_user.id}_1_{datetime.datetime.now()}'
    db_order.add_order(order_id,
                       callback.message.text.split('\n')[0].split('Город|')[1],
                       callback.message.text.split('\n')[1].split('Количество человек|')[1],
                       callback.message.text.split('\n')[2].split('Минималка (часов)|')[1],
                       callback.message.text.split('\n')[3].split('Адрес|')[1],
                       callback.message.text.split('\n')[4].split('Время прибытия|')[1],
                       callback.message.text.split('\n')[6].split('Время работы (часов)|')[1],
                       callback.message.text.split('\n')[7].split('Оплата в час (руб.)|')[1],
                       callback.message.text.split('\n')[5].split('Описание заказа|')[1]
                       )
    order_info = db_order.select_info_order(order_id)
    text = (f'🔧Заказ🔧\n\n'
            f'▪️<b>{order_info[3]}</b>\n▪️️<b>Нужны</b> {order_info[4]}/{start_places(order_id)} человек(а)✅\n'
            f'▪️<b>Адрес</b>:👉 <a href="https://yandex.ru/maps/?text={order_info[3]}+{order_info[6].replace(" ", "+")}">{order_info[6]}</a>\n'
            f'▪️<b>Описание</b>: {order_info[11]}\n'
            f'▪️<b>Начало</b>: {order_info[7]}\n'
            f'▪️<b>Оплата</b>: {order_info[9]} ₽/час, минимум {order_info[5]}\n'
            f'▪️<b>Примерное время работы</b>: {order_info[8]} часов\n'
            f'▪️<b>Получишь минимум</b>: {int(order_info[9]) * int(order_info[5])} руб.')
    worker_markup = types.InlineKeyboardMarkup(resize_keyboard=True)
    limit = int(order_info[4]) + 1 if int(order_info[4]) < 4 else 4
    for i in range(1, int(limit)):
        if i == 1:
            worker_markup.add(types.InlineKeyboardButton('🤝Поеду 1', callback_data=f'want_1_{order_id}'))
        else:
            worker_markup.add(types.InlineKeyboardButton(f'🤝Поедем в {i}', callback_data=f'want_{i}_{order_id}'))

    bt2 = types.InlineKeyboardButton('📞Связаться для уточнений', url='https://t.me/gregory237')
    worker_markup.add(bt2)
    for worker_id in db_worker.all_worker_id_by_city(callback.message.text.split('\n')[0].split('Город|')[1]):
        await bot.send_message(worker_id[0],
                               text, parse_mode='html', reply_markup=worker_markup)
    await callback.message.edit_text('✅Заказ успешно разослан. Ожидай откликов по заказу.🕰')


@dp.callback_query_handler(text_startswith='want')
async def work_on_order(callback: types.CallbackQuery):
    order_id = callback.data.split('_')[2] + '_' + callback.data.split('_')[3] + '_' + callback.data.split('_')[4]
    order_info = db_order.select_info_order(order_id)
    text_order = (f'▪️<b>{order_info[3]}</b>\n▪️️<b>Нужны</b> {order_info[4]}/{start_places(order_id)} человек(а)✅\n'
                  f'▪️<b>Адрес</b>:👉 <a href="https://yandex.ru/maps/?text={order_info[3]}+{order_info[6].replace(" ", "+")}">{order_info[6]}</a>\n'
                  f'▪️<b>Описание</b>: {order_info[11]}\n'
                  f'▪️<b>Начало</b>: {order_info[7]}\n'
                  f'▪️<b>Оплата</b>: {order_info[9]} ₽/час, минимум {order_info[5]}\n'
                  f'▪️<b>Примерное время работы</b>: {order_info[8]} часов\n'
                  f'▪️<b>Получишь минимум</b>: {int(order_info[9]) * int(order_info[5])} руб.')
    admin_id = callback.data.split('_')[2]
    worker_info = db_worker.info_worker(callback.from_user.id)
    confirm_worker = types.InlineKeyboardMarkup(resize_keyboard=True)
    bt1 = types.InlineKeyboardButton('✅Подтвердить заявку',
                                     callback_data=f"confirm_{callback.from_user.id}"
                                                   f"_{callback.data.split('_')[1]}"
                                                   f"_{order_id}")
    bt2 = types.InlineKeyboardButton('❌Отклонить заявку',
                                     callback_data=f"reject_{callback.from_user.id}" +
                                                   f"_{order_id}")
    confirm_worker.add(bt1, bt2)
    if has_places(order_id, int(callback.data.split("_")[1])):
        await callback.message.edit_text('✅Ваша заявка отправлена, далее с вами свяжется администратор.')
        await bot.send_message(admin_id, f'🔔На заказ:\n\n{text_order}\n\n⛑Откликнулся рабочий:\n\n'
                                         f'👤{worker_info[2]}\n'
                                         f'📞{worker_info[1]}\n'
                                         f'🚘Поедет {callback.data.split("_")[1]} человек(а)',
                               reply_markup=confirm_worker, parse_mode='html')
    else:
        await bot.answer_callback_query(callback.id, '❗️К сожалению по данной заявке уже нет столько мест.',
                                        show_alert=True)


@dp.callback_query_handler(text_startswith='confirm')
async def confirm_worker_on_order(callback: types.CallbackQuery):
    order_id = callback.data.split('_')[3] + '_' + callback.data.split('_')[4] + '_' + callback.data.split('_')[5]
    db_order.update_after_confirm(order_id,
                                  callback.data.split('_')[1], int(callback.data.split('_')[2]))
    old_order = db_order.select_info_order(order_id)
    if int(old_order[4]) - int(old_order[2]) > 0:
        db_order.add_order(
            callback.from_user.id,
            callback.data.split('_')[3] + '_' + str(int(callback.data.split('_')[4]) + 1) + '_' +
            callback.data.split('_')[5],
            old_order[3],
            str(int(old_order[4]) - int(old_order[2])),
            old_order[5],
            old_order[6],
            old_order[7],
            old_order[8],
            old_order[9],
            old_order[11],
        )
        new_order_id = callback.data.split('_')[3] + '_' + str(int(callback.data.split('_')[4]) + 1) + '_' + \
                       callback.data.split('_')[5]
        new_order = db_order.select_info_order(new_order_id)
        text = (f'🔧Заказ🔧\n\n'
                f'▪️<b>{new_order[3]}</b>\n▪️️<b>Нужны</b> {new_order[4]}/{start_places(new_order_id)} человек(а)✅\n'
                f'▪️<b>Адрес</b>:👉 <a href="https://yandex.ru/maps/?text={new_order[3]}+{new_order[6].replace(" ", "+")}">{new_order[6]}</a>\n'
                f'▪️<b>Описание</b>: {new_order[11]}\n'
                f'▪️<b>Начало</b>: {new_order[7]}\n'
                f'▪️<b>Оплата</b>: {new_order[9]} ₽/час, минимум {new_order[5]}\n'
                f'▪️<b>Примерное время работы</b>: {new_order[8]} часов\n'
                f'▪️<b>Получишь минимум</b>: {int(new_order[9]) * int(new_order[5])} руб.')
        worker_markup = types.InlineKeyboardMarkup(resize_keyboard=True)
        limit = int(new_order[4]) + 1 if int(new_order[4]) < 4 else 4
        for i in range(1, int(limit)):
            if i == 1:
                worker_markup.add(types.InlineKeyboardButton('🤝Поеду 1', callback_data=f'want_1_{new_order[0]}'))
            else:
                worker_markup.add(
                    types.InlineKeyboardButton(f'🤝Поедем в {i}', callback_data=f'want_{i}_{new_order[0]}'))

        bt2 = types.InlineKeyboardButton('📞Связаться для уточнений', url='https://t.me/gregory237')
        worker_markup.add(bt2)
        for worker_id in db_worker.all_worker_id_by_city(new_order[3]):
            if worker_id[0] != old_order[1]:
                await bot.send_message(worker_id[0], text, reply_markup=worker_markup, parse_mode='html')
    await callback.message.edit_text('🤝Заявка успешно, подтверждена. Рабочий назначен на заказ.')
    await bot.send_message(int(callback.data.split('_')[1]),
                           '🤝Вашу заявку одобрил администратор, вы назначены на заказ')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
