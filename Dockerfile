# Python ইমেজ ব্যবহার করা হচ্ছে
FROM python:3.10-slim

# Selenium এবং Chrome এর জন্য প্রয়োজনীয় ডিপেন্ডেন্সি ইনস্টল করা
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    libgbm1 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Google Chrome ইনস্টল করা
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb \
    && apt-get update && apt-get install -y ./chrome.deb \
    && rm chrome.deb

# কাজের ডিরেক্টরি সেট করা
WORKDIR /app

# ফাইলগুলো কপি করা
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# সব কোড কপি করা
COPY . .

# বোট রান করার কমান্ড
CMD ["python", "g.py"]