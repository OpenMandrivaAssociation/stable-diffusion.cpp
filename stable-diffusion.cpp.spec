%define git 20241130

Name:           stable-diffusion.cpp
Version:        0.%{git}
Release:        1
Summary:        Inference of Stable Diffusion and Flux in pure C/C++
License:        MiT
URL:            https://github.com/leejet/stable-diffusion.cpp

Source0:        stable-diffusion.cpp-20241130.tar.xz

# GGML was pulled as submodule
#BuildRequires:	pkgconfig(ggml)
BuildRequires:	curl-devel
BuildRequires:	cmake(libzip)
BuildRequires:  pkgconfig(openblas)
BuildRequires:  pkgconfig(vulkan)
BuildRequires:  glslang-devel
BuildRequires:  pkgconfig(shaderc)
BuildRequires:  glslc
BuildSystem:	cmake
BuildOption:	-DSD_USE_VULKAN=1
BuildOption:	-DSD_BUILD_SHARED_LIBS=1
BuildOption:	-DGGML_OPENMP=1
BuildOption:	-DGGML_BLAS=ON
BuildOption:	-DGGML_BLAS_VENDOR=OpenBLAS
BuildOption:	-DLLAMA_CLBLAST=ON
BuildOption:	-DGGML_MAX_NAME=128
BuildOption:	-DGGML_VULKAN:BOOL=ON
# This is intentionally x86_64 and not %{x86_64} -- znver1,
# x86_64v3, ... can do AVX
%ifarch x86_64
BuildOption:	-DGGML_AVX:BOOL=OFF
BuildOption:	-DGGML_AVX2:BOOL=OFF
BuildOption:	-DGGML_AVX512:BOOL=OFF
%else
%ifarch znver1
BuildOption:	-DGGML_AVX:BOOL=ON
BuildOption:	-DGGML_AVX2:BOOL=ON
BuildOption:	-DGGML_AVX512:BOOL=OFF
%endif
%endif

%patchlist
stable-diffusion-lib-versioning.patch

%description
Plain C/C++ implementation based on ggml, working in the same way as llama.cpp

# FIXME this is really more of a ggml-devel, stable-diffusion doesn't
# install its own headers
%package devel
Summary:	Development files for working with stable-diffusion
Group:		Development/C++ and C
Requires:	%{name} = %{EVRD}

%description devel
Development files for working with stable-diffusion

%prep
%autosetup -n %{name}-%{git} -p1
  
#__ln -s %_sourcedir/%name-%version %_builddir/%_sourcedir
#sed -i '4a     find_package(PkgConfig) \
#pkg_check_modules(ggml REQUIRED IMPORTED_TARGET ggml)' CMakeLists.txt
#sed -i 's|NOT TARGET ggml|TARGET ggml|g' CMakeLists.txt
  
%files
%license LICENSE
%doc README.md
%{_bindir}/sd
%{_bindir}/vulkan-shaders-gen
%{_libdir}/libggml*
%{_libdir}/libstable-diffusion.so*

%files devel
%{_includedir}/ggml*
