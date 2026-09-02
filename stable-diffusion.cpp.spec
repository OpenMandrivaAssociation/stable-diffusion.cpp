# stable-diffusion.cpp on the system ggml package (libggml + dlopen
# backends). Do not compile bundled ggml: backends live in ggml /
# ggml-backend-*.

# Out-of-tree cmake/ninja can leave empty debugsourcefiles.list.
%undefine _debugsource_packages

%bcond_without examples
%if %{with examples}
%global build_examples ON
%else
%global build_examples OFF
%endif

# Upstream tags as master-N-githash; N is the build number.
%global upstream_tag	master-841-6b3edaa

Summary:		Diffusion model inference in C/C++ (stable-diffusion.cpp)
Name:			stable-diffusion.cpp
# Old snapshot was Version: 0.20241130, which rpmvercmp ranks above 0.820.
Epoch:			1
Version:		0.841
Release:		1
License:		MIT
Group:			Sciences/Other
URL:			https://github.com/leejet/stable-diffusion.cpp
Source0:		https://github.com/leejet/stable-diffusion.cpp/archive/refs/tags/%{upstream_tag}/stable-diffusion.cpp-%{upstream_tag}.tar.gz
# Private ggml_cgraph layout (opaque in the public headers). Must match
# the system libggml. Refresh from ggml-0.22.0/src/ggml-impl.h when
# bumping ggml (current drop-in already matches 0.22.0).
Source1:		ggml-impl.h
Patch0:			0001-soversion-and-fallback-version.patch
# leejet/ggml has extra I8 kernels. Distro ggml 0.22 ships them
# (GGML_HAS_I8_TENSORWISE); this fallback still covers a stock
# ggml-org without the kernels.
Patch1:			0002-system-ggml-i8-fallbacks.patch

# Prefer -O3 over distro -Os for the inference hot path
%global optflags %{optflags} -O3

BuildRequires:	cmake(ggml) >= 0.22.0
BuildRequires:	git-core
# SD_USE_SYSTEM_WEBP — WebM stays off (no pkgconfig(libwebm) in cooker)
BuildRequires:	pkgconfig(libwebp)
BuildRequires:	pkgconfig(libwebpmux)

Requires:	%{mklibname ggml}%{?_isa} >= 0.22.0
Recommends:	ggml-backend-blas%{?_isa}
Recommends:	ggml-backend-vulkan%{?_isa}
Suggests:	ggml-backend-opencl%{?_isa}
Suggests:	ggml-backend-hip%{?_isa}

# ggml-config.cmake lists optional backends as hard deps
%global __requires_exclude cmake\\((hip|roc|mkl|intelsycl|cudatoolkit|CUDAToolkit|dnnl|DNNL|openvino|OpenVINO|sycl|SYCL).*

BuildSystem:	cmake
BuildOption:	-DCMAKE_C_COMPILER=clang
BuildOption:	-DCMAKE_CXX_COMPILER=clang++
BuildOption:	-DSD_USE_SYSTEM_GGML:BOOL=ON
BuildOption:	-DSD_BUILD_SHARED_LIBS:BOOL=ON
BuildOption:	-DSD_BUILD_EXAMPLES=%{build_examples}
# Backends come from the system ggml plugins; do not compile another copy.
BuildOption:	-DSD_VULKAN:BOOL=OFF
BuildOption:	-DSD_OPENCL:BOOL=OFF
BuildOption:	-DSD_HIPBLAS:BOOL=OFF
BuildOption:	-DSD_CUDA:BOOL=OFF
BuildOption:	-DSD_WEBP:BOOL=ON
BuildOption:	-DSD_USE_SYSTEM_WEBP:BOOL=ON
BuildOption:	-DSD_WEBM:BOOL=OFF
# pnpm + network; ABF builders are offline.
BuildOption:	-DSD_SERVER_BUILD_FRONTEND:BOOL=OFF

%description
stable-diffusion.cpp runs Stable Diffusion, Flux, Wan and related
image (and video) models. Tensor kernels come from the system ggml
package; optional accelerators are separate:

* ggml-backend-blas — OpenBLAS
* ggml-backend-vulkan — Vulkan
* ggml-backend-opencl — OpenCL
* ggml-backend-hip — AMD ROCm/HIP

The CLI (sd / sd-cli) is in %{name}-examples. The HTTP server
is in %{name}-server.

%package devel
Summary:	Development files for %{name}
Group:		Development/C++
Requires:	%{name}%{?_isa} = %{EVRD}
Requires:	cmake(ggml)

%description devel
Headers, pkg-config and CMake package config for stable-diffusion.cpp.
Requires system ggml (cmake(ggml)).

%if %{with examples}
%package server
Summary:	HTTP inference server for %{name}
Group:		Servers
Requires:	%{name}%{?_isa} = %{EVRD}

%description server
HTTP server (sd-server) for stable-diffusion.cpp. OpenAI-style
(/v1/images/generations), Automatic1111 (/sdapi/v1/txt2img) and
native /sdcpp/v1 routes. Built without the pnpm frontend (ABF has
no network); the JSON API still works.

Config: %{_sysconfdir}/sysconfig/sd-server
Unit:	stable-diffusion.service (default 127.0.0.1:8082, not
	upstream 1234, so it can run next to llama-server and
	whisper.service)

  systemctl enable --now stable-diffusion.service

If MODEL / DIFFUSION_MODEL are unset, the unit picks the first
readable .gguf/.safetensors/.ckpt/.pt under MODEL_DIRS
(/srv/ai then %{_datarootdir}/stable-diffusion.cpp/models).
Split pipelines (Flux, Z-Image, Qwen-Image, Wan) need
DIFFUSION_MODEL plus VAE / LLM / CLIP_L / T5XXL — do not rely
on the auto-pick for those.

There is no built-in API key. Do not bind HOST to a public
address without a reverse proxy.

List ggml devices:  sd-server --list-devices

To generate (after a model is loaded):

  curl http://127.0.0.1:8082/v1/images/generations \
    -H "Content-Type: application/json" \
    -d '{"prompt":"a cat","size":"512x512"}'

  curl http://127.0.0.1:8082/sdapi/v1/txt2img \
    -H "Content-Type: application/json" \
    -d '{"prompt":"a cat","width":512,"height":512}'

%package examples
Summary:	CLI tools for %{name}
Group:		Sciences/Other
Requires:	%{name}%{?_isa} = %{EVRD}

%description examples
CLI tools (sd, sd-cli) for stable-diffusion.cpp.

  sd-cli -m /srv/ai/sd15.safetensors -p "a cat" -o out.png
%endif

%prep
%autosetup -p1 -n stable-diffusion.cpp-%{upstream_tag}

# Empty submodule checkouts; backends and codecs come from the system.
# Keep a ggml-impl.h drop-in so graph-cut can see ggml_cgraph fields
# (not installed by ggml-devel).
rm -rf ggml thirdparty/libwebp thirdparty/libwebm
mkdir -p ggml/src
cp %{S:1} ggml/src/ggml-impl.h
find . -name '.gitignore' -delete 2>/dev/null || true

%if %{with examples}
%install -a
ln -sf sd-cli %{buildroot}%{_bindir}/sd
mkdir -p %{buildroot}%{_datarootdir}/%{name}/models

mkdir -p %{buildroot}%{_unitdir} %{buildroot}%{_sysconfdir}/sysconfig
mkdir -p %{buildroot}%{_libexecdir}/stable-diffusion.cpp
cat >%{buildroot}%{_unitdir}/stable-diffusion.service <<'UNIT'
[Unit]
Description=Image-generation HTTP server (stable-diffusion.cpp)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
# Wrapper sources the sysconfig (multiline MODEL_CANDIDATES).
# Do not use EnvironmentFile — systemd cannot parse a multiline list.
ExecStart=%{_libexecdir}/stable-diffusion.cpp/sd-server-start
KillMode=process
Restart=on-failure
RestartSec=5s

# Unprivileged, no extra caps. Model file must be readable by this user
# (e.g. mode 0644 under /srv/ai — /home is hidden, see ProtectHome).
DynamicUser=yes
SupplementaryGroups=render video
UMask=0077
NoNewPrivileges=yes
CapabilityBoundingSet=
AmbientCapabilities=
RestrictSUIDSGID=yes
RestrictRealtime=yes
LockPersonality=yes
ProtectHostname=yes
ProtectClock=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectProc=invisible
RestrictNamespaces=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK
SystemCallArchitectures=native
RemoveIPC=yes

# /usr /boot /etc read-only; /home /root invisible. Private /tmp.
# Models: /srv/ai is visible read-only ("-" = skip if missing).
# Extra trees: drop-in  ReadOnlyPaths=-/other/models
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateUsers=no
ReadOnlyPaths=-/srv/ai
# Mesa/Vulkan shader cache, HIP dumps. Writable CWD: ProtectSystem=strict
# makes / read-only; %C is the CacheDirectory (not /var/cache/sd-server
# nested again — StateDirectory is unused on purpose).
CacheDirectory=sd-server
WorkingDirectory=%%C
Environment=XDG_CACHE_HOME=%{_localstatedir}/cache/sd-server

# GPU: DRM render node + KFD (ROCm). No MemoryDenyWriteExecute —
# Vulkan/HIP compile executable code.
DevicePolicy=closed
DeviceAllow=/dev/null rw
DeviceAllow=/dev/zero rw
DeviceAllow=/dev/urandom r
DeviceAllow=/dev/random r
DeviceAllow=char-drm rw
DeviceAllow=/dev/dri rw
DeviceAllow=/dev/kfd rw

[Install]
WantedBy=multi-user.target
UNIT

cat >%{buildroot}%{_libexecdir}/stable-diffusion.cpp/sd-server-start <<'SH'
#!/bin/bash
# Resolve a diffusion model and exec sd-server.
# Sourced config: /etc/sysconfig/sd-server
set -u

sysconfig=${SD_SYSCONFIG:-/etc/sysconfig/sd-server}
# shellcheck source=/dev/null
[ -r "$sysconfig" ] && . "$sysconfig"

log() { printf 'sd-server: %s\n' "$*" >&2; }

readable() { [ -f "$1" ] && [ -r "$1" ]; }

# First readable path in a whitespace-separated list (globs allowed).
pick_from_candidates() {
	local cand f
	shopt -s nullglob
	for cand in $1; do
		case "$cand" in
		\#*) continue ;;
		esac
		for f in $cand; do
			if readable "$f"; then
				printf '%s\n' "$f"
				return 0
			fi
		done
	done
	return 1
}

# First regular checkpoint under MODEL_DIRS. Extensions match
# sd-server (gguf, safetensors, ckpt, pt/pth). .sft is usually a VAE.
pick_from_dirs() {
	local dir ext f
	local -a dirs
	read -r -a dirs <<< "$1"
	shopt -s nullglob
	for dir in "${dirs[@]}"; do
		[ -z "$dir" ] && continue
		[ -d "$dir" ] || continue
		for ext in gguf safetensors ckpt pt pth; do
			for f in "${dir%/}"/*."$ext"; do
				if readable "$f"; then
					printf '%s\n' "$f"
					return 0
				fi
			done
		done
	done
	return 1
}

require_file() {
	local name=$1 path=$2
	[ -z "$path" ] && return 0
	if ! readable "$path"; then
		log "$name=$path is not a readable file"
		exit 1
	fi
}

model=${MODEL:-}
diffusion=${DIFFUSION_MODEL:-}

require_file MODEL "$model"
require_file DIFFUSION_MODEL "$diffusion"
require_file VAE "${VAE:-}"
require_file LLM "${LLM:-}"
require_file CLIP_L "${CLIP_L:-}"
require_file CLIP_G "${CLIP_G:-}"
require_file T5XXL "${T5XXL:-}"
if [ -n "${LORA_DIR:-}" ] && { [ ! -d "$LORA_DIR" ] || [ ! -r "$LORA_DIR" ]; }; then
	log "LORA_DIR=$LORA_DIR is not a readable directory"
	exit 1
fi

if [ -z "$model" ] && [ -z "$diffusion" ]; then
	if [ -n "${MODEL_CANDIDATES:-}" ]; then
		if ! model=$(pick_from_candidates "$MODEL_CANDIDATES"); then
			log "none of MODEL_CANDIDATES is readable"
			exit 1
		fi
	else
		dirs=${MODEL_DIRS:-"/srv/ai /usr/share/stable-diffusion.cpp/models"}
		if ! model=$(pick_from_dirs "$dirs"); then
			log "no .gguf/.safetensors/.ckpt model found under: $dirs"
			log "drop a model in /srv/ai or set MODEL= / DIFFUSION_MODEL="
			exit 1
		fi
	fi
fi

[ -n "$model" ] && log "using --model $model"
[ -n "$diffusion" ] && log "using --diffusion-model $diffusion"

if [ -n "${SD_PRINT_MODEL:-}" ]; then
	printf '%s\n' "${model:-$diffusion}"
	exit 0
fi

cmd=(/usr/bin/sd-server)
[ -n "${HOST:-}" ] && cmd+=(--listen-ip "$HOST")
[ -n "${PORT:-}" ] && cmd+=(--listen-port "$PORT")
[ -n "$model" ] && cmd+=(--model "$model")
[ -n "$diffusion" ] && cmd+=(--diffusion-model "$diffusion")
[ -n "${VAE:-}" ] && cmd+=(--vae "$VAE")
[ -n "${LLM:-}" ] && cmd+=(--llm "$LLM")
[ -n "${CLIP_L:-}" ] && cmd+=(--clip_l "$CLIP_L")
[ -n "${CLIP_G:-}" ] && cmd+=(--clip_g "$CLIP_G")
[ -n "${T5XXL:-}" ] && cmd+=(--t5xxl "$T5XXL")
[ -n "${LORA_DIR:-}" ] && cmd+=(--lora-model-dir "$LORA_DIR")
if [ -n "${SD_OPTIONS:-}" ]; then
	# Intentional split: SD_OPTIONS is a flag string.
	# shellcheck disable=SC2206
	extra=( $SD_OPTIONS )
	cmd+=("${extra[@]}")
fi

exec "${cmd[@]}"
SH
chmod 0755 %{buildroot}%{_libexecdir}/stable-diffusion.cpp/sd-server-start

cat >%{buildroot}%{_sysconfdir}/sysconfig/sd-server <<'CFG'
# Diffusion weights (.gguf, .safetensors, .ckpt, .pt).
# The unit hides /home and /root (ProtectHome=yes). Packaged files
# under /usr/share/stable-diffusion.cpp/models are visible
# (ProtectSystem=strict leaves /usr readable). /srv/ai is extra
# (ReadOnlyPaths=-/srv/ai; "-" means the unit still starts if that
# directory is absent). Files must be readable by the service
# (e.g. chmod 0644). Extra trees: drop-in
#   ReadOnlyPaths=-/other/models
#
# Resolution, first match wins:
#   1. MODEL= / DIFFUSION_MODEL=   exact paths (error if missing)
#   2. MODEL_CANDIDATES            whitespace-separated paths/globs
#   3. first *.{gguf,safetensors,ckpt,pt,pth} in MODEL_DIRS
# At least one of --model or --diffusion-model is required.
# Auto-pick is for a single full checkpoint in those dirs. Split
# pipelines (Flux / Z-Image / Qwen-Image / Wan) need the extra
# encoder/VAE paths set explicitly.
# Full checkpoint (SD 1.5 / SDXL / SD3):
#MODEL=/srv/ai/sd15.safetensors
# Split pipeline:
#DIFFUSION_MODEL=/srv/ai/z_image_turbo.safetensors
#VAE=/srv/ai/ae.sft
#LLM=/srv/ai/qwen_3_4b.safetensors
#CLIP_L=/srv/ai/clip_l.safetensors
#CLIP_G=/srv/ai/clip_g.safetensors
#T5XXL=/srv/ai/t5xxl.safetensors
#LORA_DIR=/srv/ai/loras
#MODEL_CANDIDATES="/srv/ai/flux.gguf /srv/ai/sdxl.safetensors"
MODEL_DIRS="/srv/ai /usr/share/stable-diffusion.cpp/models"
# sd-server has no --api-key. Anyone who can reach HOST:PORT can
# generate images. Keep HOST on loopback or put a reverse proxy
# with auth in front.
HOST=127.0.0.1
# 8082 so this can run next to llama-server (8080) and whisper (8081).
# Upstream default for a manual sd-server is 1234.
PORT=8082
# GPU: ggml backends are loaded automatically (Vulkan, HIP/ROCm, …).
# List devices:         sd-server --list-devices
# Device map:           SD_OPTIONS="--backend diffusion=Vulkan0,vae=cpu"
# Flash attention + keep weights in RAM when VRAM is tight:
SD_OPTIONS="--diffusion-fa --offload-to-cpu"
CFG
%endif

%files
%license LICENSE
%{_libdir}/libstable-diffusion.so.*

%files devel
%doc README.md
%{_includedir}/stable-diffusion.h
%{_libdir}/libstable-diffusion.so
%{_libdir}/cmake/stable-diffusion/
%{_libdir}/pkgconfig/stable-diffusion.pc

%if %{with examples}
%files server
%{_bindir}/sd-server
%{_libexecdir}/stable-diffusion.cpp/sd-server-start
%{_unitdir}/stable-diffusion.service
%config(noreplace) %{_sysconfdir}/sysconfig/sd-server

%files examples
%{_bindir}/sd
%{_bindir}/sd-cli
%dir %{_datarootdir}/%{name}
%dir %{_datarootdir}/%{name}/models
%endif
