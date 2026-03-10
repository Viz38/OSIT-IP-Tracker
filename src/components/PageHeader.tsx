import React from 'react';

interface PageHeaderProps {
    title: string;
    subtitle?: string;
    children?: React.ReactNode;
    className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, children, className = "" }) => {
    return (
        <div className={`page-header ${className}`}>
            <div>
                <h1>{title}</h1>
                {subtitle && <p className="subtitle">{subtitle}</p>}
            </div>
            {children && <div className="header-actions">{children}</div>}
        </div>
    );
};
