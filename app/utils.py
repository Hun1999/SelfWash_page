from datetime import datetime
import pytz

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))
