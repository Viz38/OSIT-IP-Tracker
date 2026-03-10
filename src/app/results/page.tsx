"use client";

import React, { useEffect, useState } from 'react';
import { PageHeader } from '@/components/PageHeader';
import { supabase } from '@/lib/supabase';
import { useRouter } from 'next/navigation';

interface Target {
    id: number;
    company: string;
    domain: string;
    ip_address: string;
    location: string;
    provider: string;
    status_code: string;
    last_fetched: string;
}

export default function ResultsPage() {
    const [targets, setTargets] = useState<Target[]>([]);
    const [loading, setLoading] = useState(true);
    const [fetching, setFetching] = useState(false);
    const router = useRouter();

    const fetchTargets = async () => {
        setLoading(true);
        const { data, error } = await supabase
            .table('targets')
            .select('*')
            .order('company', { ascending: true });

        if (data) setTargets(data);
        setLoading(false);
    };

    useEffect(() => {
        fetchTargets();
    }, []);

    const handleFetchData = async () => {
        setFetching(true);
        try {
            const resp = await fetch('/api/fetch', { method: 'POST' });
            const data = await resp.json();
            if (data.status === 'success') {
                fetchTargets();
            } else {
                alert('Error fetching intel.');
            }
        } catch (err) {
            alert('Network error occurred.');
        } finally {
            setFetching(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this target?')) return;

        const { error } = await supabase.table('targets').delete().eq('id', id);
        if (!error) {
            setTargets(targets.filter(t => t.id !== id));
        } else {
            alert('Error deleting target.');
        }
    };

    const handleExport = () => {
        const headers = ['Company', 'Domain', 'IP Address', 'Location', 'Provider', 'HTTP Status', 'Last Fetched'];
        const rows = targets.map(t => [
            t.company,
            t.domain,
            t.ip_address,
            t.location,
            t.provider,
            t.status_code,
            t.last_fetched
        ]);

        const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", "detective_pradeep_results.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div>
            <PageHeader
                title="Detective Pradeep Results"
                subtitle="Tracked intel for all your registered targets."
            >
                <button onClick={handleExport} className="btn btn-secondary">⬇️ Export CSV</button>
                <button
                    id="fetch-btn"
                    onClick={handleFetchData}
                    className="btn btn-primary"
                    disabled={fetching}
                >
                    {fetching ? '⏳ Fetching intel...' : '🔄 Fetch Data'}
                </button>
            </PageHeader>

            <div className="card-custom table-card overflow-x-auto">
                <table className="results-table">
                    <thead>
                        <tr>
                            <th>Company</th>
                            <th>Domain</th>
                            <th>IP Address</th>
                            <th>Location</th>
                            <th>Provider</th>
                            <th>Status</th>
                            <th>Last Fetched</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan={8} className="text-center p-8">Loading intel...</td></tr>
                        ) : targets.length === 0 ? (
                            <tr><td colSpan={8} className="text-center no-data">No targets added yet. Go add some!</td></tr>
                        ) : (
                            targets.map((target) => (
                                <tr key={target.id}>
                                    <td>{target.company}</td>
                                    <td className="mono">
                                        <a href={`http://${target.domain}`} target="_blank" className="text-blue-500 font-medium no-underline hover:underline">
                                            {target.domain}
                                        </a>
                                    </td>
                                    <td>
                                        {target.ip_address === "Pending Fetch" ? (
                                            <span className="badge badge-pending">Pending</span>
                                        ) : target.ip_address === "Resolution Failed" ? (
                                            <span className="badge badge-error">Failed</span>
                                        ) : (
                                            <span className="badge badge-success mono">{target.ip_address}</span>
                                        )}
                                    </td>
                                    <td className="mono text-[0.8rem]">{target.location}</td>
                                    <td className="mono text-[0.8rem] max-w-[150px] overflow-hidden text-ellipsis whitespace-nowrap" title={target.provider}>
                                        {target.provider}
                                    </td>
                                    <td>
                                        {target.status_code === "Pending" ? (
                                            <span className="badge badge-pending">Pending</span>
                                        ) : ["Offline", "Timeout", "Error"].includes(target.status_code) ? (
                                            <span className="badge badge-error">{target.status_code}</span>
                                        ) : target.status_code.startsWith('2') ? (
                                            <span className="badge badge-success">{target.status_code}</span>
                                        ) : (
                                            <span className="badge bg-yellow-100 text-yellow-800">{target.status_code}</span>
                                        )}
                                    </td>
                                    <td className="mono text-[0.75rem] text-slate-500">{target.last_fetched}</td>
                                    <td>
                                        <button
                                            onClick={() => handleDelete(target.id)}
                                            className="btn btn-danger py-1 px-2 text-[0.75rem]"
                                        >
                                            🗑️ Delete
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
