# Maintainer: shinrax2
_pkgname=per-device-application-volume
pkgname=pdav-git
pkgver=0.0.1
pkgrel=1
pkgdesc="user daemon to automatically save and restore application volume settings based on default output device for pulseaudio/pipewire-pulse"
arch=(any)
url="https://github.com/shinrax2/per-device-application-volume"
license=('MIT')
depends=('python', 'python-pulsectl', 'systemd', 'pipewire-pulse', 'libpulse')
source=("git+https://github.com/shinrax2/per-device-application-volume.git")
md5sums=('SKIP')

pkgver() {
    cd $_pkgname
    printf "%s" "$(git describe --long | sed 's/^v//;s/\([^-]*-g\)/r\1/;s/-/./g')"
}

package() {
    cd $_pkgname
    install -Dm755 "$_pkgname_short" \
        -t "$pkgdir/usr/bin"
    install -Dm644 LICENSE \
        "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 pdav.service \
        "$pkgdir/etc/systemd/user/pdav.service"
}
