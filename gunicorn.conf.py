import os


bind = f"0.0.0.0:{os.getenv('PORT', '5002')}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("WEB_THREADS", "4"))
timeout = 30
accesslog = "-"
errorlog = "-"
