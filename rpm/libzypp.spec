Name:           libzypp
License:        GPLv2+
Summary:        Package, Patch, Pattern, and Product Management
Version:        17.9.0
Release:        1
Source:         %{name}-%{version}.tar.bz2
Source1:        %{name}-rpmlintrc
Patch1:         0001-Set-downloadusedeltarpmalwaystrue.patch
Patch2:         0002-Set-rpminstallexcludedocs--yes-Save-space-on.patch
Patch3:         0003-Ensure-that-the-destination-path-for-applyi.patch
Patch4:         0004-Set-unrestricted-auth-curl-option.patch
Patch5:         0005-disable-doc.patch
Patch6:         0006-libzypp-Enable-netrcoptional-on-libcurl-to-allow-for.patch
Patch7:         0007-Set-GPG-homedir-when-reading-signatures.patch
Patch8:         0008-MediaCurl-Fix-leaking-fd.patch
BuildRequires:  cmake
BuildRequires:  openssl-devel
# Need boost > 1.53 for string_ref utility
BuildRequires:  boost-devel >= 1.53.0
BuildRequires:  doxygen
BuildRequires:  gcc-c++ >= 4.6
BuildRequires:  gettext-devel
BuildRequires:  libxml2-devel
BuildRequires:  pkgconfig(libproxy-1.0)
BuildRequires:  libsolv-devel >= 0.6.8
Requires:       libsolv-tools >= 0.6.8
Requires:       libsolv0 >= 0.6.8
Requires:       lsof
BuildRequires:  glib2-devel
BuildRequires:  popt-devel
BuildRequires:  rpm-devel
BuildRequires:  gpgme-devel
Requires:       gpgme
BuildRequires:  curl-devel

%description
Package, Patch, Pattern, and Product Management

Authors:
--------
    Michael Andres <ma@suse.de>
    Jiri Srain <jsrain@suse.cz>
    Stefan Schubert <schubi@suse.de>
    Duncan Mac-Vicar <dmacvicar@suse.de>
    Klaus Kaempf <kkaempf@suse.de>
    Marius Tomaschewski <mt@suse.de>
    Stanislav Visnovsky <visnov@suse.cz>
    Ladislav Slezak <lslezak@suse.cz>

%package devel
Requires:       libzypp = %{version}
Requires:       libxml2-devel
Requires:       openssl-devel
Requires:       rpm-devel
Requires:       glibc-devel
Requires:       zlib-devel
Requires:       bzip2
Requires:       popt-devel
Requires:       boost-devel >= 1.60.0
Requires:       libstdc++-devel
Requires:       cmake
Requires:       curl-devel
Requires:       libsolv-devel
Summary:        Package, Patch, Pattern, and Product Management - developers files

%description -n libzypp-devel
Package, Patch, Pattern, and Product Management - developers files

Authors:
--------
    Michael Andres <ma@suse.de>
    Jiri Srain <jsrain@suse.cz>
    Stefan Schubert <schubi@suse.de>
    Duncan Mac-Vicar <dmacvicar@suse.de>
    Klaus Kaempf <kkaempf@suse.de>
    Marius Tomaschewski <mt@suse.de>
    Stanislav Visnovsky <visnov@suse.cz>
    Ladislav Slezak <lslezak@suse.cz>

%prep
%autosetup -p1 -n %{name}-%{version}/upstream

# Use correct libexecdir
find -type f -exec sed -i -e "s|/usr/lib/zypp|%{_libexecdir}/zypp|g" {} ';'
find -type f -exec sed -i -e "s|\${CMAKE_INSTALL_PREFIX}/lib/zypp|\${CMAKE_INSTALL_PREFIX}/libexec/zypp|g" {} ';'

%build
# Relocate all the dirs in /var/cache/zypp to /home/.zypp-cache
sed -i -r 's/^#(.*)\/var\/cache\/zypp/\1\/home\/.zypp-cache/g' ./zypp.conf
mkdir -p build
cd build

# There is gcc bug that prevents using gdwarf-4 atm.
export CFLAGS="$CFLAGS -gdwarf-2"
export CXXFLAGS="$CXXFLAGS -gdwarf-2"

cmake -DCMAKE_INSTALL_PREFIX=%{_prefix} \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_SKIP_RPATH=1 \
      -DUSE_TRANSLATION_SET=${TRANSLATION_SET:-zypp} \
      ..
make %{?_smp_mflags} VERBOSE=1
make -C po %{?_smp_mflags} translations

%if 0%{?run_testsuite}
  make -C tests %{?_smp_mflags}
  pushd tests
  LD_LIBRARY_PATH=$PWD/../zypp:$LD_LIBRARY_PATH ctest .
  popd
%endif

%install
rm -rf "$RPM_BUILD_ROOT"
cd build
make install DESTDIR=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/zypp/repos.d
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/zypp/services.d
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/zypp/vendors.d
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/zypp/multiversion.d
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/zypp/systemCheck.d
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/zypp
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/zypp/plugins
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/zypp/plugins/appdata
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/zypp/plugins/commit
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/zypp/plugins/services
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/zypp/plugins/system
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/zypp/plugins/urlresolver
mkdir -p $RPM_BUILD_ROOT%{_sharedstatedir}/zypp
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/zypp
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/cache/zypp

make -C po install DESTDIR=$RPM_BUILD_ROOT
# Create filelist with translations
cd ..
%{find_lang} zypp

%post
/sbin/ldconfig
if [ -f /var/cache/zypp/zypp.db ]; then rm /var/cache/zypp/zypp.db; fi

# convert old lock file to new
# TODO make this a separate file?
# TODO run the sript only when updating form pre-11.0 libzypp versions
LOCKSFILE=%{_sysconfdir}/zypp/locks
OLDLOCKSFILE=%{_sysconfdir}/zypp/locks.old

is_old(){
  # if no such file, exit with false (1 in bash)
  test -f ${LOCKSFILE} || return 1
  TEMP_FILE=`mktemp`
  cat ${LOCKSFILE} | sed '/^\#.*/ d;/.*:.*/d;/^[^[a-zA-Z\*?.0-9]*$/d' > ${TEMP_FILE}
  if [ -s ${TEMP_FILE} ]
  then
    RES=0
  else
    RES=1
  fi
  rm -f ${TEMP_FILE}
  return ${RES}
}

append_new_lock(){
  case "$#" in
    1 )
  echo "
solvable_name: $1
match_type: glob
" >> ${LOCKSFILE}
;;
    2 ) #TODO version
  echo "
solvable_name: $1
match_type: glob
version: $2
" >> ${LOCKSFILE}
;;
    3 ) #TODO version
  echo "
solvable_name: $1
match_type: glob
version: $2 $3
" >> ${LOCKSFILE}
  ;;
esac
}

die() {
  echo $1
  exit 1
}

if is_old ${LOCKSFILE}
  then
  mv -f ${LOCKSFILE} ${OLDLOCKSFILE} || die "cannot backup old locks"
  cat ${OLDLOCKSFILE}| sed "/^\#.*/d"| while read line
  do
    append_new_lock $line
  done
fi

%postun -p /sbin/ldconfig

%files -f zypp.lang
%defattr(-,root,root)
%dir               %{_sysconfdir}/zypp
%dir               %{_sysconfdir}/zypp/repos.d
%dir               %{_sysconfdir}/zypp/services.d
%dir               %{_sysconfdir}/zypp/vendors.d
%dir               %{_sysconfdir}/zypp/multiversion.d
%dir               %{_sysconfdir}/zypp/systemCheck.d
%config %{_sysconfdir}/zypp/zypp.conf
%config %{_sysconfdir}/zypp/systemCheck
%config %{_sysconfdir}/logrotate.d/zypp-history.lr
%dir               %{_sharedstatedir}/zypp
%dir               %{_localstatedir}/log/zypp
%dir               %{_localstatedir}/cache/zypp
%{_libexecdir}/zypp
%{_datadir}/zypp
%{_bindir}/*
%{_libdir}/libzypp*so.*
%exclude %{_sysconfdir}/zypp/needreboot

%files devel
%defattr(-,root,root,-)
%{_libdir}/libzypp.so
%{_includedir}/zypp
%{_datadir}/cmake/Modules/*
%{_libdir}/pkgconfig/libzypp.pc
