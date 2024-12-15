Name:           stable-diffusion.cpp
Version:        0
Release:        0
Summary:Inference of Stable Diffusion and Flux in pure C/C++
# FIXME: Select a correct license from https://github.com/openSUSE/spec-cleaner#spdx-licenses
License:        MiT
URL:            https://github.com/leejet/stable-diffusion.cpp.git
Source:	_service
BuildRequires:	gcc-c++
BuildRequires:	pkgconfig(ggml)
BuildRequires:	cmake-full
BuildRequires:	curl-devel
BuildRequires:	cmake(libzip)
%description


Plain C/C++ implementation based on ggml, working in the same way as llama.cpp

%prep

%setup -q -n %_sourcedir/%name-%version -T -D
%__ln -s %_sourcedir/%name-%version %_builddir/%_sourcedir
sed -i '4a     find_package(PkgConfig) \
pkg_check_modules(ggml REQUIRED IMPORTED_TARGET ggml)' CMakeLists.txt
sed -i 's|NOT TARGET ggml|TARGET ggml|g' CMakeLists.txt
%build
%cmake -DSD_USE_VULKAN=1 -DSD_BUILD_SHARED_LIBS=1 -DGGML_OPENMP=1 \
-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS -DLLAMA_CLBLAST=ON  -DGGML_MAX_NAME=128 \
-DGGML_VULKAN=1
%cmake_build

%install
%cmake_install


%files
%license LICENSE
%doc README.md
