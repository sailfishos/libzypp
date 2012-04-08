%define run_testsuite 0
Name:           libzypp
License:        GPL v2 or later
Group:          System/Packages
AutoReqProv:    on
Summary:        Package, Patch, Pattern, and Product Management
Version:        11.1.0
Release:        1
Source:         %{name}-%{version}.tar.bz2
Source1:        %{name}-rpmlintrc
Source2:        libzypp.conf
BuildRequires:  cmake
BuildRequires:  libudev-devel
BuildRequires:  libsolv-devel
BuildRequires:  openssl-devel
BuildRequires:  boost-devel curl-devel doxygen gcc-c++ gettext-devel libxml2-devel
BuildRequires:  expat-devel
BuildRequires:  dbus-glib-devel glib2-devel popt-devel rpm-devel
BuildRequires:  pkgconfig(libproxy-1.0)
Requires:       gnupg2
Requires:       libsolv-tools

Patch0:         libzypp-11.1.0-remove-timestamp.patch

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
License:        GPL v2 or later
Requires:       libzypp == %{version}
Requires:       libxml2-devel curl-devel openssl-devel rpm-devel glibc-devel zlib-devel
Requires:       bzip2 popt-devel dbus-devel glib2-devel boost-devel libstdc++-devel
Requires:       cmake libsolv-devel
Summary:        Package, Patch, Pattern, and Product Management - developers files
Group:          System/Packages

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
%setup -q
%patch0 -p1

%build
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=%{_prefix} \
      -DDOC_INSTALL_DIR=%{_docdir} \
      -DLIB=%{_lib} \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_SKIP_RPATH=1 \
      -DUSE_TRANSLATION_SET=${TRANSLATION_SET:-zypp} \
      ..
make %{?_smp_mflags} VERBOSE=1
make -C doc/autodoc %{?_smp_mflags}
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
make -C doc/autodoc install DESTDIR=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/zypp/repos.d
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/zypp/services.d
mkdir -p $RPM_BUILD_ROOT%{_usr}/lib/zypp
mkdir -p $RPM_BUILD_ROOT%{_var}/lib/zypp
mkdir -p $RPM_BUILD_ROOT%{_var}/log/zypp
mkdir -p $RPM_BUILD_ROOT%{_var}/cache/zypp

make -C po install DESTDIR=$RPM_BUILD_ROOT
# Create filelist with translations
cd ..

install -d %{buildroot}/etc/prelink.conf.d/
install -m 644 %{SOURCE2} %{buildroot}/etc/prelink.conf.d/

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
%defattr(-,root,root,-)
%dir /etc/zypp
%dir /etc/zypp/repos.d
%dir /etc/zypp/services.d
%config(noreplace) /etc/zypp/zypp.conf
%config(noreplace) /etc/zypp/systemCheck
%config(noreplace) %{_sysconfdir}/logrotate.d/zypp-history.lr
%config(noreplace) /etc/prelink.conf.d/*
%dir %{_libdir}/zypp
%{_libdir}/zypp
%dir %{_var}/lib/zypp
%dir %{_var}/log/zypp
%dir %{_var}/cache/zypp
%{_datadir}/zypp
%{_bindir}/*
%{_libdir}/libzypp*so.*

%files devel
%defattr(-,root,root,-)
%{_libdir}/libzypp.so
%{_docdir}/%{name}
%{_includedir}/zypp
%{_datadir}/cmake/Modules/*
%{_libdir}/pkgconfig/libzypp.pc
%doc %_mandir/man5/locks.5.*
