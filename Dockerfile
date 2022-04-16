# M1 MacではデフォルトでアーキテクチャがARMのイメージをイメージを取って来てしまうため、x86-64のイメージを指定
FROM public.ecr.aws/lambda/python:3.7 as build

# chromedriverやchromiumをインストール
# chromedriverのバージョンは要check
RUN yum install -y unzip && \
    curl -SL https://chromedriver.storage.googleapis.com/86.0.4240.22/chromedriver_linux64.zip > /tmp/chromedriver.zip && \
    curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-57/stable-headless-chromium-amazonlinux-2.zip > /tmp/headless-chromium.zip && \
    unzip /tmp/chromedriver.zip -d /opt/ && \
    unzip /tmp/headless-chromium.zip -d /opt/

# メイン環境　
FROM public.ecr.aws/lambda/python:3.7

# buildイメージからdriverのバイナリ等を/opt配下にコピー(lambdaでの処理実行時に/tmpにコピーする)
COPY --from=build /opt/headless-chromium /opt/
COPY --from=build /opt/chromedriver /opt/

# RUN yum install -y https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm

# lambda実行に必要なコード等
COPY app.py ./
RUN python3 -m pip install --upgrade pip \
  && pip install selenium requests

ENV DISPLAY=:0.0

CMD ["app.lambda_handler"]