let currentMemberId = null;

let requiredConsents = [];

let currentConsentIndex = 0;

let openSocialEventId = null;

let openSocialCategory = null;

let isClubMember = null;

let membershipStatus = null;

let membershipError = null;


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

const emptyState =
    document.getElementById('calendar-empty-state');


/*
    ========================================
    TELEGRAM
    ========================================
*/

const tg = window.Telegram?.WebApp;

if (tg) {
    tg.ready();

    console.log('Telegram WebApp:', tg);
    console.log('initData:', tg.initData);
    console.log('initDataUnsafe:', tg.initDataUnsafe);
    console.log('Telegram user:', tg.initDataUnsafe?.user);
} else {
    console.log('Telegram WebApp не найден');
}


/*
    ========================================
    TELEGRAM AUTH
    ========================================
*/

async function authenticateTelegramUser() {

    if (!tg?.initData) {
        console.error(
            'Telegram initData отсутствует'
        );

        return;
    }

    try {
        const response = await fetch(
            '/api/auth/telegram/',
            {
                method: 'POST',

                headers: {
                    'Content-Type':
                        'application/json'
                },

                body: JSON.stringify({
                    init_data: tg.initData
                })
            }
        );

        const data =
            await response.json();

        isClubMember =
            data.is_club_member;

        membershipStatus =
            data.membership_status;

        membershipError =
            data.membership_error;

        requiredConsents = data.required_consents || [];

        console.log("AUTH RESPONSE:", data);
        console.log("REQUIRED CONSENTS:", data.required_consents);

        if (!response.ok) {
            console.error(
                'Telegram auth error:',
                data
            );

            return;
        }

        console.log(
            'Telegram auth success:',
            data
        );

        currentMemberId = data.member_id;

        return currentMemberId;

    } catch (error) {
        console.error(
            'Ошибка Telegram auth:',
            error
        );
    }
}


async function routeAfterAuth() {

    /*
        1. Сначала Legal Gate.
    */

    currentConsentIndex = 0;

    if (requiredConsents.length > 0) {
        showConsentScreen();
        return;
    }


    /*
        2. Потом Membership Gate.
    */

    if (!isClubMember) {
        showMembershipGate();
        return;
    }


    /*
        3. Только после обоих gate —
        календарь.
    */

    document.getElementById(
        "consent-gate"
    ).style.display = "none";

    document.getElementById(
        "membership-gate"
    ).style.display = "none";

    document.getElementById(
        "calendar-app"
    ).style.display = "block";

    await loadEvents();
}


function showConsentScreen() {
    const gate = document.getElementById("consent-gate");
    const calendarApp = document.getElementById("calendar-app");

    if (requiredConsents.length === 0) {
        gate.style.display = "none";
        calendarApp.style.display = "block";
        return;
    }

    const documentData = requiredConsents[currentConsentIndex];

    calendarApp.style.display = "none";
    gate.style.display = "flex";

    const progressBars =
        document.getElementById("consent-progress-bars");

    progressBars.innerHTML = "";

    requiredConsents.forEach((_, index) => {
        const bar = document.createElement("div");

        bar.className = "consent-progress-bar";

        if (index <= currentConsentIndex) {
            bar.classList.add("active");
        }

        progressBars.appendChild(bar);
    });

    document.getElementById("consent-progress-text").textContent =
        `${currentConsentIndex + 1} из ${requiredConsents.length}`;

    document.getElementById("consent-title").textContent =
        documentData.title;

    document.getElementById("consent-version").textContent =
        `Версия ${documentData.version}`;

    document.getElementById("consent-link").href =
        documentData.url;

    const acceptButton =
        document.getElementById("consent-accept-button");

    acceptButton.onclick = handleConsentAccept;
}


async function handleConsentAccept() {
    const acceptButton =
        document.getElementById("consent-accept-button");

    const documentData =
        requiredConsents[currentConsentIndex];

    console.log(
        "Accepting document:",
        documentData.id,
        documentData.title
    );

    acceptButton.disabled = true;
    acceptButton.textContent = "Сохраняем...";

    try {
        await acceptConsent(documentData.id);

        currentConsentIndex += 1;

        if (currentConsentIndex < requiredConsents.length) {
            acceptButton.disabled = false;
            acceptButton.textContent = "Согласен";

            showConsentScreen();
            return;
        }

        /*
         * Все документы из текущего набора приняты.
         * Проверяем backend ещё раз.
         */
        await authenticateTelegramUser();

        acceptButton.disabled = false;
        acceptButton.textContent = "Согласен";

        await routeAfterAuth();

    } catch (error) {
        console.error("Consent error:", error);

        acceptButton.disabled = false;
        acceptButton.textContent = "Попробовать ещё раз";
    }
}


/*
    ========================================
    STATE
    ========================================
*/

function showBrandState() {
    emptyState.style.display = 'flex';
    eventsPanel.classList.add('hidden');
}

function showEventState() {
    emptyState.style.display = 'none';
    eventsPanel.classList.remove('hidden');
}


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
            `/api/events/?member=${currentMemberId}`
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
                    member: currentMemberId,
                    distance: null,
                    status: status,
                    looking_for_company:
                        event.current_member_looking_for_company
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

        if (
            status === 'GOING'
        ) {
            event.going_count += 1;
        }

        if (
            status === 'THINKING'
        ) {
            event.thinking_count += 1;
        }


        /*
            Сохраняем новый статус.
        */

        event.current_member_status =
            status;


        /*
            Перерисовываем карточку.
        */

        renderCurrentEvent();

    } catch (error) {
        console.error(
            'Ошибка сохранения участия:',
            error
        );
    }
}

/*
    ========================================
    REMOVE PARTICIPATION
    ========================================
*/

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


        /*
            Уменьшаем соответствующий
            социальный счётчик.
        */

        if (
            event.current_member_status === 'GOING'
        ) {
            event.going_count =
                Math.max(
                    0,
                    event.going_count - 1
                );
        }

        if (
            event.current_member_status === 'THINKING'
        ) {
            event.thinking_count =
                Math.max(
                    0,
                    event.thinking_count - 1
                );
        }


        /*
            Если пользователь искал компанию,
            его надо убрать и из этого счётчика.
        */

        if (
            event.current_member_looking_for_company
        ) {
            event.looking_for_company_count =
                Math.max(
                    0,
                    event.looking_for_company_count - 1
                );
        }


        event.current_member_status = null;

        event.current_participation_id = null;

        event.current_member_looking_for_company = false;


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
    LOOKING FOR COMPANY
    ========================================
*/

async function toggleLookingForCompany(event) {

    /*
        Искать компанию можно только
        если пользователь уже отметил
        участие в событии.
    */

    if (!event.current_participation_id) {
        return;
    }


    const newValue =
        !event.current_member_looking_for_company;


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
                    member: currentMemberId,
                    distance: null,
                    status:
                        event.current_member_status,
                    looking_for_company:
                        newValue
                })
            }
        );


        if (!response.ok) {
            const errorData =
                await response.json();

            console.error(
                'Looking for company error:',
                errorData
            );

            return;
        }


        const participationData =
            await response.json();


        event.current_participation_id =
            participationData.id;


        /*
            Обновляем локальный счётчик.
        */

        if (newValue) {
            event.looking_for_company_count += 1;
        } else {
            event.looking_for_company_count =
                Math.max(
                    0,
                    event.looking_for_company_count - 1
                );
        }


        event.current_member_looking_for_company =
            newValue;


        renderCurrentEvent();

    } catch (error) {
        console.error(
            'Ошибка изменения поиска компании:',
            error
        );
    }
}


/*
    ========================================
    DATE HELPERS
    ========================================
*/

function formatDateKey(
    year,
    month,
    day
) {

    const monthString =
        String(month + 1).padStart(
            2,
            '0'
        );

    const dayString =
        String(day).padStart(
            2,
            '0'
        );

    return (
        `${year}-${monthString}-${dayString}`
    );
}


function getEventsForDate(dateKey) {

    return events.filter(
        event => event.date === dateKey
    );
}


function formatSelectedDate(dateKey) {

    const [
        year,
        month,
        day
    ] = dateKey
        .split('-')
        .map(Number);

    return (
        `${day} ` +
        `${monthNamesGenitive[month - 1]} ` +
        `${year}`
    );
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


    /*
        День недели первого числа.

        JS:
        0 = воскресенье
        1 = понедельник
        ...

        Наш календарь:
        0 = понедельник
        ...
        6 = воскресенье
    */

    const firstDay =
        new Date(
            currentYear,
            currentMonth,
            1
        ).getDay();

    const startOffset =
        firstDay === 0
            ? 6
            : firstDay - 1;


    const daysInMonth =
        new Date(
            currentYear,
            currentMonth + 1,
            0
        ).getDate();


    /*
        Пустые клетки перед
        первым числом месяца.
    */

    for (
        let i = 0;
        i < startOffset;
        i++
    ) {
        const emptyCell =
            document.createElement('div');

        emptyCell.className =
            'calendar-day empty';

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

        const dateKey =
            formatDateKey(
                currentYear,
                currentMonth,
                day
            );


        const dayEvents =
            getEventsForDate(dateKey);


        const dayCell =
            document.createElement('button');

        dayCell.type = 'button';

        dayCell.className =
            'calendar-day';

        dayCell.textContent =
            day;


        /*
            Сегодня.
        */

        const today =
            new Date();

        if (
            day === today.getDate() &&
            currentMonth === today.getMonth() &&
            currentYear === today.getFullYear()
        ) {
            dayCell.classList.add(
                'today'
            );
        }


        /*
            Выбранная дата.
        */

        if (
            selectedDate === dateKey
        ) {
            dayCell.classList.add(
                'selected'
            );
        }


        /*
            На этой дате есть забег.
        */

        if (
            dayEvents.length > 0
        ) {
            dayCell.classList.add(
                'has-event'
            );

            /*
                Точка / индикатор события.
            */

            const eventMarker =
                document.createElement(
                    'span'
                );

            eventMarker.className =
                'event-marker';

            dayCell.appendChild(
                eventMarker
            );
        }


        dayCell.addEventListener(
            'click',
            () => {
                selectDate(
                    dateKey
                );
            }
        );


        calendarGrid.appendChild(
            dayCell
        );
    }


    /*
        После перерисовки месяца
        сохраняем правильное состояние
        нижней части интерфейса.
    */

    if (selectedDate) {

        const [
            selectedYear,
            selectedMonth
        ] = selectedDate
            .split('-')
            .map(Number);


        if (
            selectedYear === currentYear &&
            selectedMonth - 1 === currentMonth
        ) {

            selectedDayEvents =
                getEventsForDate(
                    selectedDate
                );


            if (
                selectedDayEvents.length > 0
            ) {
                showEventState();
                renderCurrentEvent();
            } else {
                showBrandState();
            }

        } else {
            showBrandState();
        }

    } else {
        showBrandState();
    }
}


/*
    ========================================
    SELECT DATE
    ========================================
*/

function selectDate(dateKey) {

    selectedDate =
        dateKey;

    selectedDayEvents =
        getEventsForDate(
            dateKey
        );

    currentEventIndex = 0;


    /*
        Перерисовываем календарь,
        чтобы подсветить выбранный день.
    */

    renderCalendar();


    if (
        selectedDayEvents.length === 0
    ) {
        showBrandState();
        return;
    }


    eventsDate.textContent =
        formatSelectedDate(
            dateKey
        );


    showEventState();

    renderCurrentEvent();
}


/*
    ========================================
    EVENT CAROUSEL
    ========================================
*/

function previousEvent() {

    if (
        selectedDayEvents.length <= 1
    ) {
        return;
    }


    currentEventIndex -= 1;


    if (
        currentEventIndex < 0
    ) {
        currentEventIndex =
            selectedDayEvents.length - 1;
    }


    renderCurrentEvent();
}


function nextEvent() {

    if (
        selectedDayEvents.length <= 1
    ) {
        return;
    }


    currentEventIndex += 1;


    if (
        currentEventIndex >=
        selectedDayEvents.length
    ) {
        currentEventIndex = 0;
    }


    renderCurrentEvent();
}


/*
    ========================================
    CAROUSEL HEADER
    ========================================

    Стрелки и счётчик теперь живут
    непосредственно в шапке карточки.

    Поэтому их положение больше
    не зависит от высоты события:
    длинного названия, количества
    дистанций, social panel и т.д.
*/

function createCarouselHeader(event) {

    const header =
        document.createElement('div');

    header.className =
        'event-card-header';


    /*
        Левая стрелка.
    */

    const previousButton =
        document.createElement('button');

    previousButton.type =
        'button';

    previousButton.className =
        'event-carousel-arrow event-carousel-arrow-left';

    previousButton.setAttribute(
        'aria-label',
        'Предыдущее событие'
    );

    previousButton.textContent =
        '←';

    previousButton.addEventListener(
        'click',
        previousEvent
    );


    /*
        Центральная часть:
        название + счётчик карусели.
    */

    const headerContent =
        document.createElement('div');

    headerContent.className =
        'event-card-header-content';


    const title =
        document.createElement('h2');

    title.className =
        'event-title';

    title.textContent =
        event.name;


    headerContent.appendChild(
        title
    );


    /*
        Счётчик показываем только
        если на выбранную дату
        приходится больше одного события.
    */

    if (
        selectedDayEvents.length > 1
    ) {

        const counter =
            document.createElement(
                'div'
            );

        counter.className =
            'event-carousel-counter';

        counter.textContent =
            `${currentEventIndex + 1} / ${selectedDayEvents.length}`;

        headerContent.appendChild(
            counter
        );
    }


    /*
        Правая стрелка.
    */

    const nextButton =
        document.createElement(
            'button'
        );

    nextButton.type =
        'button';

    nextButton.className =
        'event-carousel-arrow event-carousel-arrow-right';

    nextButton.setAttribute(
        'aria-label',
        'Следующее событие'
    );

    nextButton.textContent =
        '→';

    nextButton.addEventListener(
        'click',
        nextEvent
    );


    /*
        При единственном событии
        стрелки оставляем в DOM,
        но скрываем через класс.

        Это сохраняет геометрию
        шапки одинаковой.
    */

    if (
        selectedDayEvents.length <= 1
    ) {
        previousButton.classList.add(
            'hidden'
        );

        nextButton.classList.add(
            'hidden'
        );
    }


    header.appendChild(
        previousButton
    );

    header.appendChild(
        headerContent
    );

    header.appendChild(
        nextButton
    );


    return header;
}


/*
    ========================================
    EVENT CARD
    ========================================
*/

function renderCurrentEvent() {

    eventCardContainer.innerHTML = '';


    if (
        selectedDayEvents.length === 0
    ) {
        showBrandState();
        return;
    }


    const event =
        selectedDayEvents[
            currentEventIndex
        ];


    const card =
        document.createElement('article');

    card.className =
        'event-card';


    /*
        Шапка события.

        Здесь теперь находятся:
        ← название →
        и счётчик 1 / N.
    */

    const carouselHeader =
        createCarouselHeader(
            event
        );

    card.appendChild(
        carouselHeader
    );


    /*
        Город.
    */

    if (event.city) {

        const city =
            document.createElement('div');

        city.className =
            'event-city';

        city.textContent =
            event.city;

        card.appendChild(
            city
        );
    }


    /*
        Дистанции.
    */

    if (
        Array.isArray(
            event.distances
        ) &&
        event.distances.length > 0
    ) {

        const distances =
            document.createElement(
                'div'
            );

        distances.className =
            'event-distances';


        event.distances.forEach(
            distance => {

                const badge =
                    document.createElement(
                        'span'
                    );

                badge.className =
                    'distance-badge';


                /*
                    Если backend отдаёт name,
                    показываем его.

                    Иначе используем
                    числовую дистанцию.
                */

                if (
                    distance.name
                ) {
                    badge.textContent =
                        distance.name;
                } else {
                    badge.textContent =
                        `${distance.distance} км`;
                }


                distances.appendChild(
                    badge
                );
            }
        );


        card.appendChild(
            distances
        );
    }


    /*
        Кнопки участия.
    */

    const participationControls =
        document.createElement(
            'div'
        );

    participationControls.className =
        'participation-controls';


    const goingButton =
        document.createElement(
            'button'
        );

    goingButton.type =
        'button';

    goingButton.className =
        'participation-button';

    goingButton.textContent =
        'Я еду';


    if (
        event.current_member_status ===
        'GOING'
    ) {
        goingButton.classList.add(
            'active'
        );
    }


    goingButton.addEventListener(
        'click',
        () => {
            setParticipationStatus(
                event,
                'GOING'
            );
        }
    );


    const thinkingButton =
        document.createElement(
            'button'
        );

    thinkingButton.type =
        'button';

    thinkingButton.className =
        'participation-button';

    thinkingButton.textContent =
        'Думаю';


    if (
        event.current_member_status ===
        'THINKING'
    ) {
        thinkingButton.classList.add(
            'active'
        );
    }


    thinkingButton.addEventListener(
        'click',
        () => {
            setParticipationStatus(
                event,
                'THINKING'
            );
        }
    );


    participationControls.appendChild(
        goingButton
    );

    participationControls.appendChild(
        thinkingButton
    );


    card.appendChild(
        participationControls
    );

        /*
        Кнопка "Ищу компанию"
        появляется только после того,
        как пользователь отметил участие.
    */

    if (
        event.current_member_status
    ) {

        const companyButton =
            document.createElement(
                'button'
            );

        companyButton.type =
            'button';

        companyButton.className =
            'company-button';

        companyButton.textContent =
            event.current_member_looking_for_company
                ? 'Ищу компанию ✓'
                : 'Ищу компанию';


        if (
            event.current_member_looking_for_company
        ) {
            companyButton.classList.add(
                'active'
            );
        }


        companyButton.addEventListener(
            'click',
            () => {
                toggleLookingForCompany(
                    event
                );
            }
        );


        card.appendChild(
            companyButton
        );


        /*
            Снять отметку.
        */

        const removeButton =
            document.createElement(
                'button'
            );

        removeButton.type =
            'button';

        removeButton.className =
            'remove-participation-button';

        removeButton.textContent =
            'Снять отметку';


        removeButton.addEventListener(
            'click',
            () => {
                removeParticipation(
                    event
                );
            }
        );


        card.appendChild(
            removeButton
        );
    }


    /*
        ========================================
        SOCIAL TABS
        ========================================
    */

    const socialTabs =
        document.createElement(
            'div'
        );

    socialTabs.className =
        'event-social-tabs';


    /*
        Едут.
    */

    const goingSocialButton =
        document.createElement(
            'button'
        );

    goingSocialButton.type =
        'button';

    goingSocialButton.dataset.category =
        'going';

    goingSocialButton.textContent =
        `👥 Едут: ${event.going_count}`;


    goingSocialButton.addEventListener(
        'click',
        () => {
            toggleSocialPanel(
                event.id,
                'going'
            );
        }
    );


    /*
        Думают.
    */

    const thinkingSocialButton =
        document.createElement(
            'button'
        );

    thinkingSocialButton.type =
        'button';

    thinkingSocialButton.dataset.category =
        'thinking';

    thinkingSocialButton.textContent =
        `🤔 Думают: ${event.thinking_count}`;


    thinkingSocialButton.addEventListener(
        'click',
        () => {
            toggleSocialPanel(
                event.id,
                'thinking'
            );
        }
    );


    /*
        Ищут компанию.
    */

    const companySocialButton =
        document.createElement(
            'button'
        );

    companySocialButton.type =
        'button';

    companySocialButton.dataset.category =
        'company';

    companySocialButton.textContent =
        `🙋 Ищут компанию: ${event.looking_for_company_count}`;


    companySocialButton.addEventListener(
        'click',
        () => {
            toggleSocialPanel(
                event.id,
                'company'
            );
        }
    );


    socialTabs.appendChild(
        goingSocialButton
    );

    socialTabs.appendChild(
        thinkingSocialButton
    );

    socialTabs.appendChild(
        companySocialButton
    );


    card.appendChild(
        socialTabs
    );


    /*
        Панель со списком участников.
    */

    const socialPanel =
        document.createElement(
            'div'
        );

    socialPanel.id =
        `social-panel-${event.id}`;

    socialPanel.className =
        'event-social-panel';

    socialPanel.style.display =
        'none';


    card.appendChild(
        socialPanel
    );


    /*
        Если до перерисовки карточки
        была открыта social-категория
        именно этого события,
        восстанавливаем её.
    */

    if (
        openSocialEventId === event.id &&
        openSocialCategory
    ) {

        const activeButton =
            socialTabs.querySelector(
                `[data-category="${openSocialCategory}"]`
            );

        if (activeButton) {
            activeButton.classList.add(
                'active'
            );
        }


        socialPanel.style.display =
            'block';

        socialPanel.innerHTML =
            '<div class="social-empty">Загрузка...</div>';


        loadEventParticipants(
            event.id,
            openSocialCategory
        )
            .then(data => {

                /*
                    Карточка могла уже
                    переключиться на другое событие.
                */

                const currentPanel =
                    document.getElementById(
                        `social-panel-${event.id}`
                    );

                if (!currentPanel) {
                    return;
                }


                updateSocialCount(
                    event,
                    openSocialCategory,
                    data.count
                );


                renderSocialParticipants(
                    currentPanel,
                    data.participants
                );
            })
            .catch(error => {

                console.error(
                    error
                );

                const currentPanel =
                    document.getElementById(
                        `social-panel-${event.id}`
                    );

                if (currentPanel) {
                    currentPanel.innerHTML =
                        '<div class="social-empty">Не удалось загрузить участников</div>';
                }
            });
    }


    /*
        Готовая карточка.
    */

    eventCardContainer.appendChild(
        card
    );
}


/*
    ========================================
    SOCIAL API
    ========================================
*/

async function loadEventParticipants(
    eventId,
    category
) {

    const response =
        await fetch(
            `/api/events/${eventId}/participants/?category=${category}`
        );


    const data =
        await response.json();


    if (!response.ok) {

        console.error(
            'Participants API error:',
            data
        );

        throw new Error(
            'Не удалось загрузить участников'
        );
    }


    return data;
}


/*
    ========================================
    SOCIAL COUNTERS
    ========================================
*/

function updateSocialCount(
    event,
    category,
    count
) {

    if (
        category === 'going'
    ) {
        event.going_count =
            count;
    }


    if (
        category === 'thinking'
    ) {
        event.thinking_count =
            count;
    }


    if (
        category === 'company'
    ) {
        event.looking_for_company_count =
            count;
    }
}


/*
    ========================================
    SOCIAL PANEL
    ========================================
*/

async function toggleSocialPanel(
    eventId,
    category
) {

    const panel =
        document.getElementById(
            `social-panel-${eventId}`
        );


    if (!panel) {
        return;
    }


    const socialTabs =
        panel.previousElementSibling;


    const tabButtons =
        socialTabs.querySelectorAll(
            'button'
        );


    /*
        Повторный клик на уже
        открытую категорию:
        закрываем её.
    */

    if (
        openSocialEventId === eventId &&
        openSocialCategory === category
    ) {

        panel.innerHTML = '';

        panel.style.display =
            'none';


        tabButtons.forEach(
            button => {
                button.classList.remove(
                    'active'
                );
            }
        );


        openSocialEventId = null;

        openSocialCategory = null;


        return;
    }


    /*
        Запоминаем новое
        открытое состояние.
    */

    openSocialEventId =
        eventId;

    openSocialCategory =
        category;


    /*
        Снимаем active
        со всех вкладок.
    */

    tabButtons.forEach(
        button => {
            button.classList.remove(
                'active'
            );
        }
    );


    /*
        Подсвечиваем выбранную.
    */

    const activeButton =
        socialTabs.querySelector(
            `[data-category="${category}"]`
        );


    if (activeButton) {
        activeButton.classList.add(
            'active'
        );
    }


    panel.style.display =
        'block';

    panel.innerHTML =
        '<div class="social-empty">Загрузка...</div>';


    try {

        const data =
            await loadEventParticipants(
                eventId,
                category
            );


        /*
            Синхронизируем локальный
            объект event со свежим count
            от backend.
        */

        const event =
            events.find(
                item =>
                    item.id === eventId
            );


        if (event) {

            updateSocialCount(
                event,
                category,
                data.count
            );


            /*
                Обновляем текст именно
                активной вкладки без
                полной перерисовки карточки.
            */

            if (activeButton) {

                if (
                    category === 'going'
                ) {
                    activeButton.textContent =
                        `👥 Едут: ${data.count}`;
                }


                if (
                    category === 'thinking'
                ) {
                    activeButton.textContent =
                        `🤔 Думают: ${data.count}`;
                }


                if (
                    category === 'company'
                ) {
                    activeButton.textContent =
                        `🙋 Ищут компанию: ${data.count}`;
                }
            }
        }


        renderSocialParticipants(
            panel,
            data.participants
        );


    } catch (error) {

        console.error(
            error
        );


        panel.innerHTML =
            `
                <div class="social-empty">
                    Не удалось загрузить участников
                </div>
            `;
    }
}


/*
    ========================================
    SOCIAL PARTICIPANTS
    ========================================
*/

function renderSocialParticipants(
    panel,
    participants
) {

    if (
        !Array.isArray(participants) ||
        participants.length === 0
    ) {

        panel.innerHTML =
            `
                <div class="social-empty">
                    Пока никого нет
                </div>
            `;

        return;
    }


    panel.innerHTML =
        participants
            .map(
                participant => {

                    const username =
                        participant.username
                            ? `@${participant.username}`
                            : '';


                    const displayName =
                        participant.display_name ||
                        participant.first_name ||
                        participant.username ||
                        'Участник';


                    const firstLetter =
                        displayName
                            .charAt(0)
                            .toUpperCase();


                    /*
                        Аватар Telegram,
                        если backend его знает.
                    */

                    const avatar =
                        participant.photo_url
                            ? `
                                <div class="social-participant-avatar">
                                    <img
                                        src="${participant.photo_url}"
                                        alt=""
                                    >
                                </div>
                            `
                            : `
                                <div class="social-participant-avatar">
                                    <div class="social-participant-avatar-placeholder">
                                        ${firstLetter}
                                    </div>
                                </div>
                            `;


                    return `
                        <div class="social-participant">

                            ${avatar}

                            <div class="social-participant-info">

                                <div class="social-participant-name">
                                    ${displayName}
                                </div>

                                ${
                                    username
                                        ? `
                                            <div class="social-participant-username">
                                                ${username}
                                            </div>
                                        `
                                        : ''
                                }

                            </div>

                        </div>
                    `;
                }
            )
            .join('');
}


/*
    ========================================
    MONTH NAVIGATION
    ========================================
*/

prevMonthButton.addEventListener(
    'click',
    () => {

        currentMonth -= 1;


        if (
            currentMonth < 0
        ) {
            currentMonth = 11;
            currentYear -= 1;
        }


        selectedDate = null;

        selectedDayEvents = [];

        currentEventIndex = 0;

        openSocialEventId = null;

        openSocialCategory = null;


        renderCalendar();
    }
);


nextMonthButton.addEventListener(
    'click',
    () => {

        currentMonth += 1;


        if (
            currentMonth > 11
        ) {
            currentMonth = 0;
            currentYear += 1;
        }


        selectedDate = null;

        selectedDayEvents = [];

        currentEventIndex = 0;

        openSocialEventId = null;

        openSocialCategory = null;


        renderCalendar();
    }
);

/*
    ========================================
    LEGAL CONSENT API
    ========================================
*/

async function acceptConsent(
    documentId
) {

    const response =
        await fetch(
            '/api/legal/consents/',
            {
                method: 'POST',

                headers: {
                    'Content-Type':
                        'application/json'
                },

                body: JSON.stringify({
                    document_id:
                        documentId,

                    init_data:
                        tg.initData
                })
            }
        );


    const data =
        await response.json();


    console.log(
        'CONSENT RESPONSE:',
        data
    );


    if (!response.ok) {

        throw new Error(
            data.error ||
            'Не удалось сохранить согласие'
        );
    }


    return data;
}


/*
    ========================================
    MEMBERSHIP GATE
    ========================================
*/

function showMembershipGate() {

    const consentGate =
        document.getElementById(
            'consent-gate'
        );

    const membershipGate =
        document.getElementById(
            'membership-gate'
        );

    const calendarApp =
        document.getElementById(
            'calendar-app'
        );


    consentGate.style.display =
        'none';

    calendarApp.style.display =
        'none';

    membershipGate.style.display =
        'flex';


    console.log(
        'Membership denied:',
        membershipStatus,
        membershipError
    );
}


/*
    ========================================
    START
    ========================================
*/

async function startApp() {

    await authenticateTelegramUser();

    await routeAfterAuth();
}


startApp();