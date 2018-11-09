FROM {{cookiecutter.repo_name}}-base
RUN set -x \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive \
       apt-get install -y --no-install-recommends \
           postgresql-common \
    && sed -ri 's/#(create_main_cluster) .*$/\1 = false/' \
       /etc/postgresql-common/createcluster.conf \
    && DEBIAN_FRONTEND=noninteractive \
       apt-get install -y --no-install-recommends \
           postgresql-9.6 \
           postgresql-contrib-9.6

ENV PATH /usr/lib/postgresql/9.6/bin:$PATH
