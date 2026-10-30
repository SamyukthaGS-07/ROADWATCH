FROM eclipse-temurin:8-jdk-jammy

ARG HADOOP_VERSION=3.2.3

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 procps net-tools curl ca-certificates tar && \
    rm -rf /var/lib/apt/lists/*

ENV HADOOP_HOME=/opt/hadoop
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=/opt/hadoop/bin:/opt/hadoop/sbin:$PATH

RUN curl -fL \
    https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz \
    -o /tmp/hadoop.tar.gz && \
    tar -xzf /tmp/hadoop.tar.gz -C /opt && \
    mv /opt/hadoop-${HADOOP_VERSION} /opt/hadoop && \
    rm /tmp/hadoop.tar.gz

RUN mkdir -p /data/namenode /data/datanode /opt/hadoop/logs /workspace

WORKDIR /workspace
