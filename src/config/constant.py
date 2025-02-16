CBOE_URL = 'https://cdn.cboe.com/data/us/options/market_statistics/symbol_reference/cone-all-series.csv'

PROVIDER_LIST = ['CBOE', 'Barchart']

#Memory Config

PERSISTENCE_TYPE = 'session'  #session, local

#UTC config
CBOE_CLOSE_UTC = '21_59'
UTC = 'Etc/GMT-1'

UTC_DICT = {
    'Europe/Paris': 'Europe/Paris',
    'Europe/London': 'Europe/London',
    'Europe/Berlin': 'Europe/Berlin',
    'Europe/Madrid': 'Europe/Madrid',
    'Europe/Rome': 'Europe/Rome',
    'America/Chicago': 'America/Chicago',
    'America/New York': 'America/New_York',
    'America/Los Angeles': 'America/Los_Angeles',
    'America/Toronto': 'America/Toronto',
    'Asia/Tokyo': 'Asia/Tokyo',
    'Asia/Shanghai': 'Asia/Shanghai',
    'Asia/Dubai': 'Asia/Dubai',
    'Australia/Sydney': 'Australia/Sydney',
}

UTC_NAME = {
    'Etc/GMT+12': 'UTC-12:00',
    'Etc/GMT+11': 'UTC-11:00',
    'Etc/GMT+10': 'UTC-10:00',
    'Etc/GMT+9': 'UTC-09:00',
    'Etc/GMT+8': 'UTC-08:00',
    'Etc/GMT+7': 'UTC-07:00',
    'Etc/GMT+6': 'UTC-06:00',
    'Etc/GMT+5': 'UTC-05:00',
    'Etc/GMT+4': 'UTC-04:00',
    'Etc/GMT+3': 'UTC-03:00',
    'Etc/GMT+2': 'UTC-02:00',
    'Etc/GMT+1': 'UTC-01:00',
    'Etc/GMT': 'UTC+00:00',
    'Etc/GMT-1': 'UTC+01:00',
    'Etc/GMT-2': 'UTC+02:00',
    'Etc/GMT-3': 'UTC+03:00',
    'Etc/GMT-4': 'UTC+04:00',
    'Etc/GMT-5': 'UTC+05:00',
    'Etc/GMT-6': 'UTC+06:00',
    'Etc/GMT-7': 'UTC+07:00',
    'Etc/GMT-8': 'UTC+08:00',
    'Etc/GMT-9': 'UTC+09:00',
    'Etc/GMT-10': 'UTC+10:00',
    'Etc/GMT-11': 'UTC+11:00',
    'Etc/GMT-12': 'UTC+12:00',
}