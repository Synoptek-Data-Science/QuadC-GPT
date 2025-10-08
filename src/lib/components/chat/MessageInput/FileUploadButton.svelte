<script>
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';
	
	const dispatch = createEventDispatcher();
	
	export let disabled = false;
	export let accept = '*/*';
	export let uploadUrl = '/api/v1/files/upload';
	
	let fileInput;
	let isUploading = false;
	
	const handleFileUpload = async (files) => {
		if (!files.length) return;
		
		isUploading = true;
		const toastId = toast.loading('File uploading...', { duration: Infinity });
		
		try {
			const results = [];
			
			for (const file of files) {
				toast.loading(`Uploading ${file.name}...`, { id: toastId, duration: Infinity });
				const result = await uploadSingleFile(file);
				results.push(result);
			}
			
			toast.dismiss(toastId);
			toast.success(`${files.length} file(s) uploaded successfully!`);
			dispatch('files-uploaded', { files: results });
			
		} catch (error) {
			toast.dismiss(toastId);
			toast.error(`Upload failed: ${error.message}`);
		} finally {
			isUploading = false;
		}
	};
	
	const uploadSingleFile = (file) => {
		return new Promise((resolve, reject) => {
			const xhr = new XMLHttpRequest();
			const formData = new FormData();
			formData.append('file', file);
			
			xhr.onload = () => xhr.status === 200 ? resolve(JSON.parse(xhr.responseText || '{}')) : reject(new Error(`HTTP ${xhr.status}`));
			xhr.onerror = () => reject(new Error('Network error'));
			
			xhr.open('POST', uploadUrl);
			xhr.send(formData);
		});
	};
</script>

<button
	class="upload-btn"
	class:uploading={isUploading}
	{disabled}
	on:click={() => !disabled && !isUploading && fileInput.click()}
	title={isUploading ? 'Uploading...' : 'Upload file'}
>
	<input
		bind:this={fileInput}
		type="file"
		{accept}
		multiple
		on:change={(e) => handleFileUpload(Array.from(e.target.files))}
		style="display: none;"
	/>
	
	{#if isUploading}
		<svg class="spin" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
		</svg>
	{:else}
		<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/>
		</svg>
	{/if}
</button>

<style>
	.upload-btn {
		padding: 0.5rem;
		border: none;
		background: transparent;
		cursor: pointer;
		border-radius: 6px;
		display: flex;
		align-items: center;
		transition: background 0.2s ease;
	}
	
	.upload-btn:hover {
		background: rgba(0, 0, 0, 0.05);
	}
	
	.upload-btn:disabled,
	.upload-btn.uploading {
		cursor: not-allowed;
		opacity: 0.6;
	}
	
	.spin {
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
</style>