/*
    ВРЕМЕННО!

    Пока Telegram-auth у нас нет,
    считаем текущим пользователем ClubMember id=2.
*/
const testMemberId = 2;


/*
    ========================================
    DOM
    ========================================
*/

const calendarTitle =
    document.querySelector('.calendar-title');

const calendarGrid =
    document.querySelector('.calendar-grid');

const prevMonthButton =
    document.querySelector('.prev-month');

const nextMonthButton =
    document.querySelector('.next-month');

const eventsPanel =
    document.querySelector('.events-panel');

const eventsDate =
    document.querySelector('.events-date');

const eventCardContainer =
    document.querySelector('.event-card-container');

const eventPrevButton =
    document.querySelector('.event-prev');

const eventNextButton =
    document.querySelector('.event-next');

const eventCounter =
    document.querySelector('.event-counter');


/*
    ========================================
    STATE
    ========================================
*/

let events = [];

const now = new Date();

let currentYear =
    now.getFullYear();

let currentMonth =
    now.getMonth();

let selectedDate = null;

let selectedDayEvents = [];

let currentEventIndex = 0;


/*
    ========================================
    MONTH NAMES
    ========================================
*/

const monthNames = [
    'Январь',
    'Февраль',
    'Март',
    'Апрель',
    'Май',
    'Июнь',
    'Июль',
    'Август',
    'Сентябрь',
    'Октябрь',
    'Ноябрь',
    'Декабрь'
];

const monthNamesGenitive = [
    'января',
    'февраля',
    'марта',
    'апреля',
    'мая',
    'июня',
    'июля',
    'августа',
    'сентября',
    'октября',
    'ноября',
    'декабря'
];


/*
    ========================================
    LOAD EVENTS
    ========================================
*/

async function loadEvents() {
    try {
        const response = await fetch(
            `/api/events/?member=${testMemberId}`
        );

        if (!response.ok) {
            throw new Error(
                `HTTP error: ${response.status}`
            );
        }

        events = await response.json();

        renderCalendar();

    } catch (error) {
        console.error(
            'Ошибка загрузки событий:',
            error
        );
    }
}


/*
    ========================================
    PARTICIPATION
    ========================================
*/

async function setParticipationStatus(
    event,
    status
) {

    /*
        Если человек нажал кнопку,
        которая уже активна,
        ничего не делаем.
    */
    if (
        event.current_member_status === status
    ) {
        return;
    }


    try {
        const response = await fetch(
            '/api/participations/',
            {
                method: 'POST',

                headers: {
                    'Content-Type':
                        'application/json'
                },

                body: JSON.stringify({
                    event: event.id,
                    member: testMemberId,
                    distance: null,
                    status: status,
                    looking_for_company: false
                })
            }
        );


        if (!response.ok) {
            const errorData =
                await response.json();

            console.error(
                'Participation error:',
                errorData
            );



            return;
        }


        const participationData =
            await response.json();

        event.current_participation_id =
            participationData.id;


        /*
            Запоминаем старый статус,
            чтобы правильно переставить
            единичку между счётчиками.
        */

        const previousStatus =
            event.current_member_status;


        /*
            Убираем пользователя
            из старого счётчика.
        */

        if (
            previousStatus === 'GOING'
        ) {
            event.going_count =
                Math.max(
                    0,
                    event.going_count - 1
                );
        }

        if (
            previousStatus === 'THINKING'
        ) {
            event.thinking_count =
                Math.max(
                    0,
                    event.thinking_count - 1
                );
        }


        /*
            Добавляем пользователя
            в новый счётчик.
        */

        if (status === 'GOING') {
            event.going_count += 1;
        }

        if (status === 'THINKING') {
            event.thinking_count += 1;
        }


        event.current_member_status =
            status;


        renderCurrentEvent();

    } catch (error) {
        console.error(
            'Ошибка изменения участия:',
            error
        );
    }
}

async function removeParticipation(event) {

    if (!event.current_participation_id) {
        return;
    }

    try {
        const response = await fetch(
            `/api/participations/${event.current_participation_id}/`,
            {
                method: 'DELETE'
            }
        );

        if (!response.ok) {
            console.error(
                'Ошибка удаления участия:',
                response.status
            );

            return;
        }

        if (event.current_member_status === 'GOING') {
            event.going_count = Math.max(
                0,
                event.going_count - 1
            );
        }

        if (event.current_member_status === 'THINKING') {
            event.thinking_count = Math.max(
                0,
                event.thinking_count - 1
            );
        }

        event.current_member_status = null;
        event.current_participation_id = null;

        renderCurrentEvent();

    } catch (error) {
        console.error(
            'Ошибка удаления участия:',
            error
        );
    }
}



/*
    ========================================
    CALENDAR
    ========================================
*/

function renderCalendar() {

    calendarGrid.innerHTML = '';

    calendarTitle.textContent =
        `${monthNames[currentMonth]} ${currentYear}`;


    const firstDay =
        new Date(
            currentYear,
            currentMonth,
            1
        );


    const daysInMonth =
        new Date(
            currentYear,
            currentMonth + 1,
            0
        ).getDate();


    /*
        JS:
        Sunday = 0
        Monday = 1

        Нам надо:
        Monday = 0
        Sunday = 6
    */

    let startOffset =
        firstDay.getDay() - 1;

    if (startOffset < 0) {
        startOffset = 6;
    }


    /*
        Пустые клетки
        перед первым числом месяца.
    */

    for (
        let i = 0;
        i < startOffset;
        i++
    ) {
        const emptyCell =
            document.createElement('div');

        emptyCell.className =
            'calendar-day';

        calendarGrid.appendChild(
            emptyCell
        );
    }


    /*
        Дни месяца.
    */

    for (
        let day = 1;
        day <= daysInMonth;
        day++
    ) {

        const cell =
            document.createElement('div');

        cell.className =
            'calendar-day';


        const dayNumber =
            document.createElement('div');

        dayNumber.className =
            'day-number';

        dayNumber.textContent =
            day;


        const dateString =
            buildDateString(
                currentYear,
                currentMonth,
                day
            );


        const dayEvents =
            events.filter(
                event =>
                    event.date ===
                    dateString
            );


        if (dayEvents.length > 0) {

            cell.classList.add(
                'has-event'
            );


            cell.addEventListener(
                'click',
                function () {

                    selectedDate =
                        dateString;

                    selectedDayEvents =
                        dayEvents;

                    currentEventIndex = 0;

                    renderCalendar();

                    openEventsPanel(
                        day
                    );
                }
            );
        }


        if (
            selectedDate ===
            dateString
        ) {
            cell.classList.add(
                'selected'
            );
        }


        cell.appendChild(
            dayNumber
        );

        calendarGrid.appendChild(
            cell
        );
    }
}


/*
    ========================================
    EVENT PANEL
    ========================================
*/

function openEventsPanel(day) {

    eventsPanel.classList.remove(
        'hidden'
    );


    eventsDate.textContent =
        `${day} ` +
        `${monthNamesGenitive[currentMonth]} ` +
        `${currentYear}`;


    renderCurrentEvent();
}


function renderCurrentEvent() {

    eventCardContainer.innerHTML = '';


    if (
        selectedDayEvents.length === 0
    ) {
        return;
    }


    const event =
        selectedDayEvents[
            currentEventIndex
        ];


    /*
        Карточка.
    */

    const card =
        document.createElement('div');

    card.className =
        'event-card';


    /*
        Название.
    */

    const title =
        document.createElement('h3');

    title.className =
        'event-name';

    title.textContent =
        event.name;

    card.appendChild(
        title
    );


    /*
        Город.
    */

    const city =
        document.createElement('div');

    city.className =
        'event-city';

    city.textContent =
        event.city;

    card.appendChild(
        city
    );


    /*
        Дистанции.
    */

    if (
        event.distances &&
        event.distances.length > 0
    ) {

        const distancesContainer =
            document.createElement('div');

        distancesContainer.className =
            'distances';


        event.distances.forEach(
            function (distance) {

                const badge =
                    document.createElement(
                        'div'
                    );

                badge.className =
                    'distance-badge';

                /*
                    Нам важнее красивое name,
                    чем голое число distance.
                */

                badge.textContent =
                    distance.name;

                distancesContainer.appendChild(
                    badge
                );
            }
        );


        card.appendChild(
            distancesContainer
        );
    }


    /*
        Счётчики участия.
    */

    const participationInfo =
        document.createElement('div');

    participationInfo.className =
        'participation-info';


    const goingInfo =
        document.createElement('span');

    goingInfo.textContent =
        `👥 Едут: ${event.going_count}`;


    const thinkingInfo =
        document.createElement('span');

    thinkingInfo.textContent =
        `🤔 Думают: ${event.thinking_count}`;


    participationInfo.appendChild(
        goingInfo
    );

    participationInfo.appendChild(
        thinkingInfo
    );


    card.appendChild(
        participationInfo
    );


    /*
        Кнопки.
    */

    const buttons =
        document.createElement('div');

    buttons.className =
        'participation-buttons';


    const goingButton =
        document.createElement('button');

    goingButton.className =
        'participation-button going-button';


    const thinkingButton =
        document.createElement('button');

    thinkingButton.className =
        'participation-button thinking-button';


    /*
        Текущий статус пользователя.
    */

    if (
        event.current_member_status ===
        'GOING'
    ) {

        goingButton.textContent =
            'Я еду ✓';

        goingButton.classList.add(
            'active'
        );


        thinkingButton.textContent =
            'Думаю';

    } else if (
        event.current_member_status ===
        'THINKING'
    ) {

        goingButton.textContent =
            'Я еду';


        thinkingButton.textContent =
            'Думаю ✓';

        thinkingButton.classList.add(
            'active'
        );

    } else {

        goingButton.textContent =
            'Я еду';

        thinkingButton.textContent =
            'Думаю';
    }


    /*
        Обработчики кнопок.
    */

    goingButton.addEventListener(
        'click',
        function () {

            setParticipationStatus(
                event,
                'GOING'
            );
        }
    );


    thinkingButton.addEventListener(
        'click',
        function () {

            setParticipationStatus(
                event,
                'THINKING'
            );
        }
    );


    buttons.appendChild(
        goingButton
    );

    buttons.appendChild(
        thinkingButton
    );
    if (event.current_member_status) {

    const removeButton =
        document.createElement('button');

    removeButton.className =
        'remove-participation-button';

    removeButton.textContent =
        'Снять отметку';

    removeButton.addEventListener(
        'click',
        function () {
            removeParticipation(event);
        }
    );

    card.appendChild(buttons);
    card.appendChild(removeButton);

    } else {

        card.appendChild(buttons);
    }




    eventCardContainer.appendChild(
        card
    );


    updateCarouselControls();
}


/*
    ========================================
    CAROUSEL
    ========================================
*/

function updateCarouselControls() {

    const total =
        selectedDayEvents.length;


    if (total <= 1) {

        eventPrevButton.classList.add(
            'hidden'
        );

        eventNextButton.classList.add(
            'hidden'
        );

        eventCounter.classList.add(
            'hidden'
        );

        return;
    }


    eventPrevButton.classList.remove(
        'hidden'
    );

    eventNextButton.classList.remove(
        'hidden'
    );

    eventCounter.classList.remove(
        'hidden'
    );


    eventCounter.textContent =
        `${currentEventIndex + 1} / ${total}`;
}


eventPrevButton.addEventListener(
    'click',
    function () {

        if (
            selectedDayEvents.length <= 1
        ) {
            return;
        }


        currentEventIndex--;


        if (currentEventIndex < 0) {
            currentEventIndex =
                selectedDayEvents.length - 1;
        }


        renderCurrentEvent();
    }
);


eventNextButton.addEventListener(
    'click',
    function () {

        if (
            selectedDayEvents.length <= 1
        ) {
            return;
        }


        currentEventIndex++;


        if (
            currentEventIndex >=
            selectedDayEvents.length
        ) {
            currentEventIndex = 0;
        }


        renderCurrentEvent();
    }
);


/*
    ========================================
    MONTH NAVIGATION
    ========================================
*/

prevMonthButton.addEventListener(
    'click',
    function () {

        currentMonth--;


        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }


        closeEventsPanel();

        renderCalendar();
    }
);


nextMonthButton.addEventListener(
    'click',
    function () {

        currentMonth++;


        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }


        closeEventsPanel();

        renderCalendar();
    }
);


function closeEventsPanel() {

    selectedDate = null;

    selectedDayEvents = [];

    currentEventIndex = 0;


    eventsPanel.classList.add(
        'hidden'
    );
}


/*
    ========================================
    HELPERS
    ========================================
*/

function buildDateString(
    year,
    month,
    day
) {

    const monthString =
        String(
            month + 1
        ).padStart(
            2,
            '0'
        );


    const dayString =
        String(
            day
        ).padStart(
            2,
            '0'
        );


    return (
        `${year}-` +
        `${monthString}-` +
        `${dayString}`
    );
}


/*
    ========================================
    START
    ========================================
*/

loadEvents();

