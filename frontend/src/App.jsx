import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, CheckCircle2, Download, RefreshCw, AlertCircle } from 'lucide-react';

export default function App() {
  const [step, setStep] = useState('upload'); 
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState({ processed: 0, total: 0, percentage: 0 });
  const [errorMsg, setErrorMsg] = useState('');
  const fileInputRef = useRef(null);


  useEffect(() => {
    let interval = null;
    if (step === 'processing' && jobId) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/jobs/${jobId}`);
          if (!res.ok) throw new Error("Falha ao verificar status.");
          const data = await res.json();
          
          setProgress({
            processed: data.processed,
            total: data.total,
            percentage: data.percentage
          });

          if (data.status === 'completed') {
            setStep('completed');
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Erro no polling:", err);
        }
      }, 500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [step, jobId]);

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;
    setFile(selectedFile);
    uploadAndStartJob(selectedFile);
  };

  const uploadAndStartJob = async (fileToUpload) => {
    setStep('processing');
    setErrorMsg('');
    setProgress({ processed: 0, total: 0, percentage: 0 });

    const formData = new FormData();
    formData.append('file', fileToUpload);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Erro ao enviar arquivo.");
      }

      setJobId(data.job_id);
      setProgress({ processed: 0, total: data.total, percentage: 0 });
    } catch (err) {
      setStep('error');
      setErrorMsg(err.message || "Erro de conexão com o servidor.");
    }
  };

  const handleDownload = () => {
    if (!jobId) return;
    window.location.href = `/api/export/${jobId}`;
  };

  const resetForm = () => {
    setStep('upload');
    setFile(null);
    setJobId(null);
    setProgress({ processed: 0, total: 0, percentage: 0 });
    setErrorMsg('');
  };

  return (
    <div className="container">
      <header className="header">
        <div className="header-badge">
          <FileSpreadsheet size={16} /> Consulta em Lote • Simples Nacional & MEI
        </div>
        <h1>Consulta de Regime Tributário</h1>
        <p>Envie sua planilha de CNPJs e obtenha o resumo atualizado em Excel</p>
      </header>

      <main className="card">
        {step === 'upload' && (
          <div 
            className="dropzone"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
            onDrop={(e) => {
              e.preventDefault();
              e.stopPropagation();
              if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                handleFileSelect(e.dataTransfer.files[0]);
              }
            }}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              className="file-input" 
              accept=".xlsx, .xls, .csv" 
              onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
            />
            <div className="dropzone-icon">
              <UploadCloud size={30} />
            </div>
            <div className="dropzone-title">Clique ou arraste sua planilha aqui</div>
            <div className="dropzone-desc">Formatos suportados: .XLSX, .XLS ou .CSV</div>
          </div>
        )}

        {step === 'processing' && (
          <div className="progress-container">
            <div className="progress-status">
              Processando empresas ({progress.processed} de {progress.total})
            </div>
            <div className="progress-sub">
              Consultando dados oficiais da Receita Federal... {progress.percentage}%
            </div>
            <div className="progress-bar-bg">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${Math.min(progress.percentage, 100)}%` }} 
              />
            </div>
          </div>
        )}

        {step === 'completed' && (
          <div className="result-container">
            <div className="result-icon">
              <CheckCircle2 size={36} />
            </div>
            <div className="result-title">Processamento Concluído!</div>
            <div className="result-desc">
              Todas as {progress.total} empresas foram consultadas com sucesso.
            </div>

            <button className="btn btn-primary" onClick={handleDownload}>
              <Download size={20} /> BAIXAR PLANILHA FINAL (.XLSX)
            </button>

            <button className="btn btn-secondary" onClick={resetForm}>
              <RefreshCw size={18} /> Consultar Outra Planilha
            </button>
          </div>
        )}

        {step === 'error' && (
          <div className="result-container">
            <div className="error-message">
              <AlertCircle size={20} style={{ marginBottom: 6 }} /><br />
              {errorMsg}
            </div>

            <button className="btn btn-secondary" onClick={resetForm} style={{ marginTop: '1.5rem' }}>
              <RefreshCw size={18} /> Tentar Novamente
            </button>
          </div>
        )}
      </main>

      <footer className="footer-credits">
        Dados fornecidos via base aberta da Receita Federal • Consulta em lote para contabilidade
      </footer>
    </div>
  );
}
