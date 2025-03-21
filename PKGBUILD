# Maintainer: shinrax2
_pkgname=per-device-application-volume
pkgname=pdav-git
pkgver=0.0.1_475a4ac
pkgrel=1
pkgdesc="user daemon to automatically save and restore application volume settings based on default output device for pulseaudio/pipewire-pulse"
arch=(any)
url="https://github.com/shinrax2/per-device-application-volume"
license=('MIT')
depends=('python>=3' 'python-pulsectl' 'systemd' 'pulse-native-provider' 'libpulse')
source=("git+https://github.com/shinrax2/per-device-application-volume.git")
md5sums=('SKIP')

pkgver() {
    cd $_pkgname
    printf "0.0.1_%s" "$(git  rev-parse --short HEAD)"
}

package() {
    cd $_pkgname
    install -Dm755 "pdav" \
        -t "$pkgdir/usr/bin"
    install -Dm644 LICENSE \
        "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 pdav.service \
        "$pkgdir/etc/systemd/user/pdav.service"
}

post_install() {
    systemctl --user daemon-reload
    systemctl --user --now enable pdav.service
}

pre_remove() {
    systemctl --user --now disable pdav.service
}
