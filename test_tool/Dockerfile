FROM golang:1.17.8-alpine3.15 as builder
WORKDIR /app
COPY main.go /app
COPY go.mod /app
RUN go build -o /boomboom && chmod +x /boomboom

FROM golang:1.17.8-alpine3.15 as runner
COPY --from=builder /boomboom /usr/bin/boomboom
WORKDIR /

ENV PORT=80
ENV HOST=reverse-proxy
ENV WORKERS=32
ENV FIXEDWAIT=10
ENTRYPOINT ["boomboom"]