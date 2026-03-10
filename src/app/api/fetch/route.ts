import { NextResponse } from 'next/server';
import dns from 'dns';
import { promisify } from 'util';
import { createClient } from '@supabase/supabase-js';

const resolve4 = promisify(dns.resolve4);

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY!; // Use service role for updates if needed, or anon if RLS allows

const supabase = createClient(supabaseUrl, supabaseServiceRoleKey);

export async function POST() {
    try {
        const { data: targets, error: fetchError } = await supabase
            .table('targets')
            .select('id, domain');

        if (fetchError || !targets) {
            return NextResponse.json({ status: 'error', message: fetchError?.message || 'No targets' }, { status: 500 });
        }

        let updatedCount = 0;

        for (const target of targets) {
            const res = {
                ip_address: "Resolution Failed",
                location: "N/A",
                provider: "N/A",
                status_code: "N/A",
                last_fetched: new Date().toISOString().replace('T', ' ').split('.')[0]
            };

            // 1. Resolve IP
            try {
                const addresses = await resolve4(target.domain);
                if (addresses && addresses.length > 0) {
                    const ip = addresses[0];
                    res.ip_address = ip;

                    // 2. Geolocation and Provider
                    try {
                        const geoResp = await fetch(`http://ip-api.com/json/${ip}`, { signal: AbortSignal.timeout(3000) });
                        if (geoResp.ok) {
                            const geoData = await geoResp.json();
                            if (geoData.status === 'success') {
                                res.location = `${geoData.city}, ${geoData.country}`;
                                res.provider = geoData.org || geoData.isp || "Unknown";
                            }
                        }
                    } catch (e) {
                        console.error(`Geo error for ${ip}:`, e);
                    }
                }
            } catch (e) {
                console.error(`DNS error for ${target.domain}:`, e);
            }

            // 3. HTTP Status Check
            try {
                const httpResp = await fetch(`http://${target.domain}`, {
                    method: 'GET',
                    redirect: 'follow',
                    signal: AbortSignal.timeout(3000)
                });
                res.status_code = httpResp.status.toString();
            } catch (e) {
                try {
                    const httpsResp = await fetch(`https://${target.domain}`, {
                        method: 'GET',
                        redirect: 'follow',
                        signal: AbortSignal.timeout(3000)
                    });
                    res.status_code = httpsResp.status.toString();
                } catch (err) {
                    res.status_code = "Offline";
                }
            }

            // Update Supabase
            await supabase.table('targets').update(res).eq('id', target.id);
            updatedCount++;
        }

        return NextResponse.json({ status: 'success', message: `Successfully updated ${updatedCount} records.` });
    } catch (error: any) {
        return NextResponse.json({ status: 'error', message: error.message }, { status: 500 });
    }
}
