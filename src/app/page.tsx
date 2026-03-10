"use client";

import React, { useState } from 'react';
import { PageHeader } from '@/components/PageHeader';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';

export default function AddTargetPage() {
    const [company, setCompany] = useState('');
    const [domain, setDomain] = useState('');
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleManualSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const { error } = await supabase.table('targets').insert({
                company: company.trim(),
                domain: domain.trim(),
                ip_address: "Pending Fetch",
                location: "Pending",
                provider: "Pending",
                status_code: "Pending",
                last_fetched: "Never"
            });

            if (error) {
                if (error.message.includes('duplicate key')) {
                    alert('This domain already exists in the tracker.');
                } else {
                    alert(`Error adding target: ${error.message}`);
                }
            } else {
                router.push('/results');
            }
        } catch (err) {
            alert('An unexpected error occurred.');
        } finally {
            setLoading(false);
        }
    };

    const handleCsvUpload = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const file = formData.get('csv_file') as File;

        if (!file) return;

        setLoading(true);
        const reader = new FileReader();
        reader.onload = async (event) => {
            const text = event.target?.result as string;
            const lines = text.split('\n');
            const batchData = [];
            let headerSkipped = false;

            for (let line of lines) {
                const parts = line.split(',');
                if (parts.length < 2) continue;

                const col1 = parts[0].trim();
                const col2 = parts[1].trim();

                if (!headerSkipped && (col1.toLowerCase() === 'company' || col1.toLowerCase() === 'name')) {
                    headerSkipped = true;
                    continue;
                }

                if (col1 && col2) {
                    batchData.push({
                        company: col1,
                        domain: col2,
                        ip_address: "Pending Fetch",
                        location: "Pending",
                        provider: "Pending",
                        status_code: "Pending",
                        last_fetched: "Never"
                    });
                }
            }

            if (batchData.length > 0) {
                // One by one to handle duplicates simply for now
                let addedCount = 0;
                let duplicateCount = 0;
                for (const item of batchData) {
                    const { error } = await supabase.table('targets').insert(item);
                    if (error) {
                        if (error.message.includes('duplicate key')) {
                            duplicateCount++;
                        }
                    } else {
                        addedCount++;
                    }
                }
                alert(`Successfully added ${addedCount} targets. ${duplicateCount} duplicates skipped.`);
                router.push('/results');
            }
            setLoading(false);
        };
        reader.readAsText(file);
    };

    return (
        <div>
            <PageHeader
                title="Add New Targets"
                subtitle="Enter a company and its domain manually, or upload a CSV file in bulk."
            />

            <div className="flex flex-wrap gap-8">
                <div className="card-custom form-card flex-1 min-w-[300px] m-0">
                    <h3 className="mb-4 text-lg font-semibold">Manual Entry</h3>
                    <form onSubmit={handleManualSubmit} className="target-form">
                        <div className="form-group">
                            <label htmlFor="company">Company Name</label>
                            <input
                                type="text"
                                id="company"
                                value={company}
                                onChange={(e) => setCompany(e.target.value)}
                                placeholder="e.g., Acme Corp"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="domain">Domain</label>
                            <input
                                type="text"
                                id="domain"
                                value={domain}
                                onChange={(e) => setDomain(e.target.value)}
                                placeholder="e.g., acme.com"
                                required
                            />
                        </div>

                        <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                            {loading ? 'Adding...' : 'Add Target'}
                        </button>
                    </form>
                </div>

                <div className="card-custom form-card flex-1 min-w-[300px] m-0">
                    <h3 className="mb-4 text-lg font-semibold">Bulk Upload CSV</h3>
                    <p className="subtitle mb-4">Upload a CSV file containing two columns: <strong>Company</strong> and <strong>Domain</strong>.</p>
                    <form onSubmit={handleCsvUpload} className="target-form">
                        <div className="form-group">
                            <label htmlFor="csv_file">Select CSV File</label>
                            <input
                                type="file"
                                id="csv_file"
                                name="csv_file"
                                accept=".csv"
                                required
                                className="p-2"
                                style={{ background: 'var(--bg-color)' }}
                            />
                        </div>

                        <button type="submit" className="btn btn-secondary btn-block" disabled={loading}>
                            {loading ? 'Uploading...' : 'Upload Targets'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
