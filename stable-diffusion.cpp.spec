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
BuildRequires:	cmake
BuildRequires:	curl-devel
BuildRequires:	cmake(libzip)
BuildRequires:  pkgconfig(openblas)
BuildRequires:  pkgconfig(vulkan)
BuildRequires:  glslang-devel
BuildRequires:  pkgconfig(shaderc)
BuildRequires:  glslc

%description
Plain C/C++ implementation based on ggml, working in the same way as llama.cpp

%prep
%autosetup -n %{name}-%{git} -p1
  
#__ln -s %_sourcedir/%name-%version %_builddir/%_sourcedir
#sed -i '4a     find_package(PkgConfig) \
#pkg_check_modules(ggml REQUIRED IMPORTED_TARGET ggml)' CMakeLists.txt
#sed -i 's|NOT TARGET ggml|TARGET ggml|g' CMakeLists.txt
  
%build
%cmake -DSD_USE_VULKAN=1 -DSD_BUILD_SHARED_LIBS=1 -DGGML_OPENMP=1 \
-DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS -DLLAMA_CLBLAST=ON  -DGGML_MAX_NAME=128 \
-DGGML_VULKAN=1
%make_build

%install
%make_install -C build


%files
%license LICENSE
%doc README.md
