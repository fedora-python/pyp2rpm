FROM fedora:rawhide

ENV PIP_NO_CACHE_DIR=off \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

LABEL summary="Image for running automatic tests of pyp2rpm in Travis CI" \
      name="pyp2rpm-tests" \
      maintainer="Michal Cyprian <mcyprian@redhat.com>"

RUN INSTALL_PKGS="gcc tox python3.6 python3.7 python3.8 python3.9 python3.10 \
                  python3-setuptools python3-pip" && \
    dnf -y install --setopt=install_weak_deps=false --setopt=tsflags=nodocs \
                   --setopt=deltarpm=false $INSTALL_PKGS && \
    dnf clean all

CMD ["/usr/bin/tox"]
