FROM python:3.13-alpine

COPY --chmod=644 --chown=nobody:nobody requirements.txt /var/tmp/requirements.txt
RUN mkdir /usr/local/app \
  && chown nobody:nobody /usr/local/app

USER nobody
WORKDIR /usr/local/app
ENV PYTHONPATH=.

RUN mkdir smtp2s3 \
  && pip install --no-cache-dir --requirement /var/tmp/requirements.txt --target .

COPY --chmod=755 --chown=nobody:nobody app.py /usr/local/app/app.py
COPY --chmod=644 --chown=nobody:nobody ./smtp2s3 /usr/local/app/smtp2s3

ENTRYPOINT [ "/usr/local/app/app.py" ]
