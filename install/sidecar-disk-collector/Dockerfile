FROM rust:1.83-alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /app
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release

FROM alpine:3.21
RUN apk add --no-cache util-linux && mkdir -p /storage
COPY --from=builder /app/target/release/cairn-disk-collector /usr/local/bin/cairn-disk-collector
WORKDIR /storage
CMD ["/usr/local/bin/cairn-disk-collector"]
