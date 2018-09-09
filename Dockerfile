FROM docker.elastic.co/elasticsearch/elasticsearch:6.2.4

ADD ./aknn /aknn
WORKDIR /aknn


# Install Java 10
# Before building this image, download the .rpm files to elasticsearch-aknn directory
#     from http://www.oracle.com/technetwork/java/javase/downloads/index.html

RUN yum -y install jdk-10.0.2_linux-x64_bin.rpm
RUN yum -y install jre-10.0.2_linux-x64_bin.rpm
ENV JAVA_HOME=/usr/java/jdk-10.0.2/


# Install gradle 4.9

RUN wget https://services.gradle.org/distributions/gradle-4.9-bin.zip
RUN mkdir /opt/gradle
RUN unzip -d /opt/gradle gradle-4.9-bin.zip
ENV PATH=$PATH:/opt/gradle/gradle-4.9/bin


# Build & install the plugin

RUN gradle clean build -x integTestRunner -x test
RUN elasticsearch-plugin install -b file:build/distributions/elasticsearch-aknn-0.0.1-SNAPSHOT.zip

WORKDIR /usr/share/elasticsearch

# Configure ElasticSearch
ENV ES_JAVA_OPTS="-Xms10g -Xmx10g"
