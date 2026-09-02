"use client";

import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { uploadDocument, type Document, type UploadProgress, SUPPORTED_FILE_TYPES, SUPPORTED_BADGES, SUPPORTED_EXTENSIONS, MAX_FILE_SIZE } from "@/lib/api/documents";
import { Upload, X, File, CheckCircle, AlertCircle, Loader2, Trash2, Eye, Download } from "lucide-react";

// ============================================================================
// DESIGN TOKENS - Consistent with Orivory's Nebulous Precision
// ============================================================================

const DESIGN = {
  colors: {
    bg: "bg-background",
    surface: "bg-white/[0.03]",
    surfaceHover: "hover:bg-white/[0.06]",
    border: "border-white/[0.08]",
    text: {
      primary: "text-white",
      secondary: "text-white/60",
      muted: "text-white/40",
    },
    accent: {
      violet: "text-violet-400",
      pink: "text-pink-400",
      gradient: "bg-gradient-to-r from-violet-400 to-pink-400",
    },
  },
  transition: "transition-all duration-300 ease-out",
};

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface DocumentUploaderProps {
  className?: string;
  workspaceId?: string;
  onUploadComplete?: (document: Document) => void;
  onUploadError?: (error: Error) => void;
  acceptedTypes?: string[];
  maxFiles?: number;
}

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

/**
 * File type icon with appropriate color
 */
function FileTypeIcon({ fileType, className }: { fileType: string; className?: string }) {
  const type = Object.entries(SUPPORTED_FILE_TYPES).find(([, config]) =>
    config.extensions.some(ext => fileType.toLowerCase().endsWith(ext))
  );
  
  const icon = type?.[1]?.icon || "📄";
  
  return (
    <span className={cn("text-2xl", className)} role="img" aria-label={type?.[1]?.label || "File"}>
      {icon}
    </span>
  );
}

/**
 * Single file item with progress
 */
function FileItem({
  file,
  progress,
  onRemove,
}: {
  file: File;
  progress?: UploadProgress;
  onRemove: () => void;
}) {
  const isUploading = progress?.status === "uploading" || progress?.status === "processing";
  const isComplete = progress?.status === "ready";
  const isError = progress?.status === "error";

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className={cn(
        "flex items-center gap-3 p-3",
        "bg-white/[0.02] border border-white/[0.05]",
        "rounded-lg"
      )}
    >
      {/* File icon */}
      <div className={cn(
        "w-10 h-10 rounded-lg flex items-center justify-center",
        "bg-white/[0.05]"
      )}>
        <FileTypeIcon fileType={file.name} />
      </div>

      {/* File info */}
      <div className="flex-1 min-w-0">
        <p className={cn("text-sm font-medium truncate", DESIGN.colors.text.primary)}>
          {file.name}
        </p>
        {isError && progress?.message ? (
          <p className={cn("text-xs text-red-400/90 truncate")} title={progress.message}>
            {progress.message.replace(/^Upload failed: \d+ - /, "").slice(0, 120)}
          </p>
        ) : (
          <p className={cn("text-xs", DESIGN.colors.text.muted)}>
            {(file.size / 1024 / 1024).toFixed(2)} MB
          </p>
        )}
      </div>

      {/* Status indicator */}
      <div className="flex items-center gap-2">
        {isUploading && (
          <>
            <Loader2 className={cn("w-4 h-4 text-violet-400 animate-spin")} />
            {progress?.progress !== undefined && (
              <div className="w-16 h-1 bg-white/[0.1] rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-violet-500 to-purple-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress.progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            )}
          </>
        )}
        
        {isComplete && (
          <CheckCircle className="w-5 h-5 text-emerald-400" />
        )}
        
        {isError && (
          <AlertCircle className="w-5 h-5 text-red-400" />
        )}

        {/* Remove button */}
        {!isUploading && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onRemove}
            className={cn(
              "p-1.5 rounded-md",
              "text-white/40 hover:text-red-400",
              "hover:bg-red-500/10",
              "transition-colors"
            )}
          >
            <Trash2 className="w-4 h-4" />
          </motion.button>
        )}
      </div>
    </motion.div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function DocumentUploader({
  className,
  workspaceId,
  onUploadComplete,
  onUploadError,
  acceptedTypes = [],
  maxFiles = 10,
}: DocumentUploaderProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [progressMap, setProgressMap] = useState<Map<string, UploadProgress>>(new Map());
  const [isDragging, setIsDragging] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Validate files
  const validateFiles = useCallback((fileList: FileList | File[]): File[] => {
    const validFiles: File[] = [];
    const errors: string[] = [];

    Array.from(fileList).slice(0, maxFiles - files.length).forEach((file) => {
      // Check size
      if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name} exceeds ${MAX_FILE_SIZE / 1024 / 1024}MB limit`);
        return;
      }

      // Check type
      const ext = "." + file.name.split(".").pop()?.toLowerCase() || "";
      const isSupported = Object.values(SUPPORTED_FILE_TYPES).some(
        (type: { extensions: string[] }) => type.extensions.includes(ext)
      );

      if (!isSupported && acceptedTypes.length === 0) {
        errors.push(`${file.name} is not a supported file type`);
        return;
      }

      validFiles.push(file);
    });

    if (errors.length > 0) {
      console.warn("File validation errors:", errors);
      // Surface to the user — previously these only hit the console and the
      // rejected files just vanished silently.
      setValidationErrors(errors);
    } else {
      setValidationErrors([]);
    }

    return validFiles;
  }, [files.length, maxFiles, acceptedTypes]);

  // Handle file selection
  const handleFiles = useCallback((selectedFiles: FileList | File[]) => {
    const validFiles = validateFiles(selectedFiles);
    setFiles((prev) => [...prev, ...validFiles].slice(0, maxFiles));
  }, [validateFiles, maxFiles]);

  // Remove file
  const handleRemove = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Upload all files
  const handleUpload = async () => {
    for (const file of files) {
      // Skip if already uploaded
      const progress = progressMap.get(file.name);
      if (progress?.status === "ready") continue;

      try {
        const document = await uploadDocument({
          file,
          workspace_id: workspaceId,
          onProgress: (prog) => {
            setProgressMap((prev) => new Map(prev).set(file.name, prog));
          },
        });

        setProgressMap((prev) => new Map(prev).set(file.name, {
          documentId: document.id,
          progress: 100,
          status: "ready",
        }));

        onUploadComplete?.(document);
      } catch (error) {
        setProgressMap((prev) => new Map(prev).set(file.name, {
          documentId: "",
          progress: 0,
          status: "error",
          message: error instanceof Error ? error.message : "Upload failed",
        }));
        onUploadError?.(error instanceof Error ? error : new Error(String(error)));
      }
    }
  };

  // Drag handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  // Upload when files are added
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const allUploaded = files.length > 0 && files.every(
    (file) => progressMap.get(file.name)?.status === "ready"
  );

  return (
    <div className={cn("flex flex-col", className)}>
      {/* Drop zone */}
      <motion.div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          "relative rounded-xl border-2 border-dashed p-8",
          "cursor-pointer",
          "transition-all duration-300",
          isDragging
            ? "border-violet-500 bg-violet-500/5"
            : "border-white/[0.1] hover:border-white/[0.2] hover:bg-white/[0.02]"
        )}
      >
        {/* Glow effect on drag */}
        {isDragging && (
          <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 to-pink-500/10 rounded-xl blur-sm" />
        )}

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.length > 0 ? acceptedTypes.join(",") : SUPPORTED_EXTENSIONS}
          onChange={handleFileInputChange}
          className="hidden"
        />

        <div className="relative z-10 text-center">
          <motion.div
            animate={{ y: isDragging ? -8 : 0 }}
            transition={{ type: "spring", stiffness: 300 }}
            className={cn(
              "w-14 h-14 mx-auto mb-4 rounded-xl",
              "bg-white/[0.05] border border-white/[0.1]",
              "flex items-center justify-center"
            )}
          >
            <Upload className={cn(
              "w-6 h-6",
              isDragging ? "text-violet-400" : "text-white/50"
            )} />
          </motion.div>

          <p className={cn("text-sm font-medium mb-1", DESIGN.colors.text.primary)}>
            {isDragging ? "Drop files here" : "Drag & drop files here"}
          </p>
          <p className={cn("text-xs", DESIGN.colors.text.muted)}>
            or click to browse
          </p>

          <div className={cn(
            "flex flex-wrap justify-center gap-2 mt-4",
            "text-[10px] text-white/30"
          )}>
            {SUPPORTED_BADGES.map((label, i) => (
              <span key={label} className="flex items-center gap-2">
                {i > 0 && <span aria-hidden="true">•</span>}
                <span>{label}</span>
              </span>
            ))}
          </div>
          <p className={cn("text-[10px] mt-2", DESIGN.colors.text.muted)}>
            Max {MAX_FILE_SIZE / 1024 / 1024}MB per file
          </p>
        </div>
      </motion.div>

      {/* File list */}
      <AnimatePresence mode="popLayout">
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-4 space-y-2"
          >
            {files.map((file, index) => (
              <FileItem
                key={`${file.name}-${index}`}
                file={file}
                progress={progressMap.get(file.name)}
                onRemove={() => handleRemove(index)}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload button */}
      {validationErrors.length > 0 && (
        <div
          role="alert"
          className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20"
        >
          <p className="text-xs font-medium text-red-400 mb-1">
            {validationErrors.length} file{validationErrors.length > 1 ? "s" : ""} rejected:
          </p>
          <ul className="text-xs text-red-400/80 list-disc list-inside">
            {validationErrors.map((err) => (
              <li key={err}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {files.length > 0 && !allUploaded && !files.some((f) => progressMap.get(f.name)?.status === "error") && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4"
        >
          <motion.button
            whileHover={{ scale: 1.02, y: -1 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleUpload}
            disabled={files.some((f) => progressMap.get(f.name)?.status === "uploading")}
            className={cn(
              "w-full py-3 px-4 rounded-xl",
              "bg-gradient-to-r from-violet-600 to-purple-600",
              "text-white font-medium text-sm",
              "shadow-lg shadow-violet-500/20",
              "hover:shadow-violet-500/30",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-all duration-300"
            )}
          >
            Upload {files.length} file{files.length > 1 ? "s" : ""}
          </motion.button>
        </motion.div>
      )}

      {/* All uploaded */}
      {allUploaded && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={cn(
            "mt-4 p-4 rounded-xl",
            "bg-emerald-500/10 border border-emerald-500/20",
            "text-center"
          )}
        >
          <CheckCircle className="w-6 h-6 text-emerald-400 mx-auto mb-2" />
          <p className={cn("text-sm font-medium text-emerald-400")}>
            All files uploaded successfully
          </p>
        </motion.div>
      )}
    </div>
  );
}

export default DocumentUploader;
