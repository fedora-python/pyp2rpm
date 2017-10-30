FROM fedora:rawhide

ENV PIP_NO_CACHE_DIR=off \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8

LABEL summary="Image for running automatic tests of pyp2rpm in Travis CI" \
      name="pyp2rpm-tests" \
      maintainer="Michal Cyprian <mcyprian@redhat.com>"

RUN INSTALL_PKGS="gcc tox python34 python35 python2-dnf python2-virtualenv \
                  python2-virtualenv-api python3-virtualenv python3-virtualenv-api" && \
    dnf -y install --setopt=install_weak_deps=false --setopt=tsflags=nodocs \
                   --setopt=deltarpm=false $INSTALL_PKGS && \
    dnf clean all

CMD ["/usr/bin/tox"]
