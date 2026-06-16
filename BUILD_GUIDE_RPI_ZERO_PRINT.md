# Паук: быстрая инструкция для распечатки (Raspberry Pi Zero)

## 1) Прошивка SD-карты

- [ ] Скачать и установить Raspberry Pi Imager: <https://www.raspberrypi.com/software/>
- [ ] Вставить SD-карту (из паука) в картридер
- [ ] Открыть Raspberry Pi Imager
- [ ] `Device`: выбрать `Raspberry Pi Zero`
- [ ] `Operating System`: выбрать `Raspberry Pi OS (32-bit)` -> `Next`
- [ ] `Storage`: выбрать нужную SD-карту
- [ ] В `OS customization` заполнить:
  - [ ] `Hostname` — имя паука в сети (латиница, например `pauk-zero`)
  - [ ] `Localisation` (можно оставить дефолт)
  - [ ] `Username` — логин для входа на паука (латиница, например `pauk`)
**Запишите на бумажку (понадобится дальше):**
- Имя паука (Hostname), например: `pauk-zero`
- Логин (Username), например: `pauk`
- Пароль от этого пользователя
  - [ ] `Wi-Fi` (домашняя сеть и пароль)
  - [ ] `Remote access`: `Enable SSH` (оставить включенным)
  - [ ] `Raspberry Pi Connect`: оставить по умолчанию
- [ ] Запустить `Write` и дождаться окончания прошивки


## 2) Первый запуск паука

- [ ] Вставить прошитую SD-карту обратно в паука
- [ ] Подключить питание от 2x18650
- [ ] Убедиться, что светодиоды мигают
- [ ] Подождать 1-2 минуты загрузки Raspberry Pi OS

## 3) Узнать IP паука (устройство должно быть в той же Wi-Fi сети)

**Важно:** в командах ниже вместо `pauk-zero` подставьте **имя паука (Hostname)**, которое вы вводили при прошивке SD-карты (шаг 1, поле Hostname).  
Пример: если вводили `pauk-zero`, в команде будет `pauk-zero.local`.

### macOS

```bash
ping pauk-zero.local
```

### Linux

```bash
ping pauk-zero.local
```

### Windows (PowerShell/CMD)

```powershell
ping pauk-zero.local
```

Если команда не находит паука, откройте список устройств в сети:

```bash
# macOS / Linux
arp -a
```

```powershell
# Windows
arp -a
```

- [ ] Записать IP-адрес паука (числа вида `192.168.1.25` — у каждого будут свои)

## 4) Подключение по SSH

**Важно:** в команде ниже:
- `pauk` — это **логин (Username)**, который вы вводили при прошивке SD-карты (шаг 1, поле User);
- `pauk-zero.local` — **имя паука (Hostname)** из того же шага;
- пароль — тот, который вы задали для этого пользователя при прошивке.

Подключение по имени паука:

```bash
ssh pauk@pauk-zero.local
```

Если по имени не получается — подключайтесь по IP из шага 3 (подставьте свой адрес):

```bash
ssh pauk@192.168.1.25
```

- [ ] Успешно зайти на Raspberry Pi по SSH

## 5) Установка проекта `pauk`

```bash
git clone https://github.com/davy1ex/juhikgh.git
cd juhikgh
chmod +x setup.sh start.sh
./setup.sh
```

- [ ] `setup.sh` завершился без ошибок

## 6) Что делать дальше

```bash
./start.sh
```

- [ ] Открыть пульт в браузере: `http://192.168.1.25:5000` (вместо `192.168.1.25` — IP из шага 3)
- [ ] Калибровка: `http://192.168.1.25:5000/calibrate`

## 7) (Опционально) автозапуск

```bash
chmod +x install-services.sh scripts/spider-ap.sh
sudo ./install-services.sh
```

- [ ] Проверить, что автозапуск установлен

## Ссылки

- Raspberry Pi Imager: <https://www.raspberrypi.com/software/>
- Репозиторий: <https://github.com/davy1ex/juhikgh>
