function getAvailabilityState(data, capacity = 10) {
  const toInt = v => Number.isFinite(+v) ? Math.max(0, +v) : NaN;

  const wait = toInt(data.redis_check_courts_queue_size) + toInt(data.redis_verify_courts_queue_size);
  const wip  = toInt(data.celery_check_courts_queue_size) + toInt(data.celery_verify_courts_queue_size);

  // валидация
  if (![wait, wip].every(Number.isFinite) || wip > capacity) {
    return { status: 'неизвестно', level: 0, reason: 'некорректные данные', metrics: { wait, wip, capacity } };
  }

  if ((wait + wip) <= 5){
    return {status:'excellent',level: 5, reason:'очередь меньше 5', metrics: { wait, wip } };
  }

  if ((wait + wip) <= 10) {
    return { status: 'good', level: 4, reason: 'очередь меньше 10', metrics: { wait, wip } };
  }

  if((wait + wip) <= 15){
    return { status: 'average', level: 3, reason: 'очередь меньше 15', metrics: { wait, wip } };
  }

  if((wait + wip) >= 15){
    return { status: 'bad', level: 1, reason: 'большая очередь', metrics: { wait, wip } };
  }
  return { status: 'unknown', level: 0, reason: 'error', metrics: { wait, wip } };
}

function getCheckTimeState(data,type) {
  const toInt = v => Number.isFinite(+v) ? Math.max(0, +v) : NaN;
  const blue_time = toInt(data.celery_court_last_check_time_blue);
  const yellow_time  = toInt(data.celery_court_last_check_time_yellow);
  
  // валидация
  if (![blue_time, yellow_time].every(Number.isFinite)) {
    return { status: 'unknown', level: 0, reason: 'некорректные данные', metrics: { blue_time, yellow_time } };
  }

  if ((blue_time === 0 && yellow_time === 0)){
    return {status:'unknown',level: 5, reason:'unknown ', metrics: { blue_time, yellow_time } };
  }

  if ((blue_time <= 60 && yellow_time <= 80)){
    return {status:'excellent',level: 5, reason:'очень быстро', metrics: { blue_time, yellow_time } };
  }

  if ((blue_time <= 120 && yellow_time <= 400)) {
    return { status: 'good', level: 4, reason: 'хорошо', metrics: { blue_time, yellow_time } };
  }

  if((blue_time <= 180 && yellow_time <= 800)){
    return { status: 'average', level: 3, reason: 'средне', metrics: { blue_time, yellow_time } };
  }

  if((blue_time <= 240 && yellow_time <= 1200)){
    return { status: 'bad', level: 1, reason: 'очень медленно', metrics: { blue_time, yellow_time } };
  }
  return { status: 'unknown', level: 0, reason: 'error', metrics: { blue_time, yellow_time } };
}

function setCourtQueueStatus(status) {
  const wave = document.querySelector('.court-queue-wave');
  wave.className = 'court-queue-wave status-' + status;
}

function setCourtCheckTimeStatus(status) {
  const wave = document.querySelector('.court-check-time-wave');
  wave.className = 'court-check-time-wave status-' + status;
}

function setTooltipData(data) {
  blue_time = Math.round(data.celery_court_last_check_time_blue);
  yellow_time = Math.round(data.celery_court_last_check_time_yellow);
  blue_text = "Мировые (Центр. Рег.): Данные отсутствуют";
  yellow_text = "Суды общ. юрисд.: Данные отсутствуют";
  if (blue_time !== 0){
    blue_text = `Мировые (Центр. Рег.): ≈ ${blue_time} сек.`;
  }
  if (yellow_time !== 0) {
    yellow_text = `Суды общ. юрисд.: ≈ ${yellow_time} сек.`;
  }

  document.getElementById('queue-status-text').innerHTML =
    `Задачи в работе: ${data.celery_check_courts_queue_size}<br>Задачи в очереди: ${data.redis_check_courts_queue_size}`;
  document.getElementById('check-time-status-text').innerHTML =
    `Среднее время проверок судов:<br>${blue_text}<br>${yellow_text}`;
}

function setTooltipDataUnavailable(){
  document.getElementById('queue-status-text').innerHTML = `Сервис недоступен`;
  document.getElementById('check-time-status-text').innerHTML = `Сервис недоступен`;
}