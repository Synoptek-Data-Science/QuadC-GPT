<script>
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';
	
	const dispatch = createEventDispatcher();
	
	export let accept = '*/*';
	export let multiple = false;
	export let maxSize = 10 * 1024 * 1024; // 10MB
	export let uploadUrl = '/api/v1/files/upload';
	
	let isDragging = false;
	let fileInput;
	let isUploading = false;
	let uploadProgress = 0;
	
	const handleFileSelect = async (files) => {
		if (!files || files.length === 0) return;
		
		isUploading = true;
		uploadProgress = 0;
		
		// Show upload starting message
		const toastId = toast.loading('File uploading...', {
			duration: Infinity,
		});
		
		try {
			const uploadedFiles = [];
			
			for (let i = 0; i < files.length; i++) {
				const file = files[i];
				
				// Validate file size
				if (file.size > maxSize) {
					throw new Error(`File "${file.name}" exceeds ${maxSize / 1024 / 1024}MB limit`);
				}
				
				// Update progress
				const baseProgress = (i / files.length) * 100;
				
				// Upload individual file
				const result = await uploadFile(file, (progress) => {
					uploadProgress = baseProgress + (progress / files.length);
					toast.loading(`Uploading... ${Math.round(uploadProgress)}%`, {
						id: toastId,
						duration: Infinity,
					});
				});
				
				uploadedFiles.push(result);
			}
			
			// Success
			toast.dismiss(toastId);
			toast.success(`${files.length} file(s) uploaded successfully!`, {
				duration: 3000,
			});
			
			dispatch('upload-success', { files: uploadedFiles });
			
		} catch (error) {
			toast.dismiss(toastId);
			toast.error(`Upload failed: ${error.message}`, {
				duration: 5000,
			});
		} finally {
			isUploading = false;
			uploadProgress = 0;
		}
	};
	
	const uploadFile = (file, onProgress) => {
		return new Promise((resolve, reject) => {
			const formData = new FormData();
			formData.append('file', file);
			
			const xhr = new XMLHttpRequest();
			
			xhr.upload.onprogress = (e) => {
				if (e.lengthComputable) {
					onProgress((e.loaded / e.total) * 100);
				}
			};
			
			xhr.onload = () => {
				if (xhr.status === 200) {
					try {
						resolve(JSON.parse(xhr.responseText));
					} catch (e) {
						resolve({ name: file.name, uploaded: true });
					}
				} else {
					reject(new Error(`HTTP ${xhr.status}`));
				}
			};
			
			xhr.onerror = () => reject(new Error('Network error'));
			
			xhr.open('POST', uploadUrl);
			xhr.send(formData);
		});
	};
	
	const handleDrop = (e) => {
		e.preventDefault();
		isDragging = false;
		const files = Array.from(e.dataTransfer.files);
		handleFileSelect(files);
	};
	
	const handleFileInputChange = (e) => {
		handleFileSelect(Array.from(e.target.files));
		e.target.value = '';
	};
</script>

<div
	class="upload-area"
	class:dragging={isDragging}
	class:uploading={isUploading}
	on:dragover={(e) => { e.preventDefault(); isDragging = true; }}
	on:dragleave={() => isDragging = false}
	on:drop={handleDrop}
	on:click={() => !isUploading && fileInput.click()}
	role="button"
	tabindex="0"
>
	<input
		bind:this={fileInput}
		type="file"
		{accept}
		{multiple}
		on:change={handleFileInputChange}
		style="display: none;"
	/>
	
	{#if isUploading}
		<div class="upload-status">
			<div class="progress-bar">
				<div class="progress" style="width: {uploadProgress}%"></div>
			</div>
			<p>Uploading... {Math.round(uploadProgress)}%</p>
		</div>
	{:else}
		<div class="upload-prompt">
			<svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
			</svg>
			<p>Drop files here or click to browse</p>
		</div>
	{/if}
</div>

<style>
	.upload-area {
		border: 2px dashed #cbd5e0;
		border-radius: 12px;
		padding: 2rem;
		text-align: center;
		cursor: pointer;
		transition: all 0.3s ease;
		background: #f8fafc;
		min-height: 120px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.upload-area:hover {
		border-color: #94a3b8;
		background: #f1f5f9;
	}
	
	.upload-area.dragging {
		border-color: #3b82f6;
		background: #eff6ff;
	}
	
	.upload-area.uploading {
		cursor: not-allowed;
		opacity: 0.8;
	}
	
	.upload-status {
		width: 100%;
		max-width: 300px;
	}
	
	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e2e8f0;
		border-radius: 4px;
		margin-bottom: 1rem;
		overflow: hidden;
	}
	
	.progress {
		height: 100%;
		background: #3b82f6;
		transition: width 0.3s ease;
	}
	
	.upload-prompt {
		color: #64748b;
	}
	
	.upload-prompt svg {
		margin: 0 auto 1rem;
		color: #94a3b8;
	}
</style>