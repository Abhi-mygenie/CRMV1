import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Users, QrCode, Plus, Star, TrendingUp, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MobileLayout } from "@/components/MobileLayout";

export default function DashboardPage() {
    const { user, api } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState(null);
    const [recentCustomers, setRecentCustomers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, customersRes] = await Promise.all([
                    api.get("/analytics/dashboard"),
                    api.get("/customers?limit=5")
                ]);
                setStats(statsRes.data);
                setRecentCustomers(customersRes.data);
            } catch (err) {
                toast.error("Failed to load dashboard");
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return (
            <MobileLayout>
                <div className="p-4 animate-pulse">
                    <div className="h-8 bg-gray-200 rounded w-48 mb-4"></div>
                    <div className="h-32 bg-gray-200 rounded-xl mb-4"></div>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="h-24 bg-gray-200 rounded-xl"></div>
                        <div className="h-24 bg-gray-200 rounded-xl"></div>
                    </div>
                </div>
            </MobileLayout>
        );
    }

    return (
        <MobileLayout>
            <div className="p-4 max-w-lg mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <p className="text-[#52525B] text-sm">Welcome back</p>
                        <h1 className="text-2xl font-bold text-[#1A1A1A] font-['Montserrat']" data-testid="restaurant-name">
                            {user?.restaurant_name}
                        </h1>
                    </div>
                    <Avatar className="w-10 h-10 bg-[#F26B33]">
                        <AvatarFallback className="bg-[#F26B33] text-white font-semibold">
                            {user?.restaurant_name?.charAt(0)}
                        </AvatarFallback>
                    </Avatar>
                </div>

                {/* Hero Stats Card */}
                <Card className="loyalty-card-gradient text-white rounded-2xl mb-4 border-0 shadow-lg" data-testid="hero-stats-card">
                    <CardContent className="p-5">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-white/80 text-sm">Total Customers</p>
                                <p className="text-4xl font-bold font-['Montserrat'] mt-1">{stats?.total_customers || 0}</p>
                            </div>
                            <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center">
                                <Users className="w-8 h-8 text-white" />
                            </div>
                        </div>
                        <div className="flex items-center mt-4 text-sm">
                            <TrendingUp className="w-4 h-4 mr-1" />
                            <span className="font-medium">+{stats?.new_customers_7d || 0} this week</span>
                        </div>
                    </CardContent>
                </Card>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-3 mb-6">
                    <div className="stats-card" data-testid="points-issued-card">
                        <div className="flex items-center gap-2 text-[#329937] mb-2">
                            <ArrowUpRight className="w-4 h-4" />
                            <span className="text-xs font-medium uppercase tracking-wider">Points Issued</span>
                        </div>
                        <p className="text-2xl font-bold text-[#1A1A1A] font-['Montserrat'] points-display">
                            {stats?.total_points_issued?.toLocaleString() || 0}
                        </p>
                    </div>
                    <div className="stats-card" data-testid="points-redeemed-card">
                        <div className="flex items-center gap-2 text-[#329937] mb-2">
                            <ArrowDownRight className="w-4 h-4" />
                            <span className="text-xs font-medium uppercase tracking-wider">Redeemed</span>
                        </div>
                        <p className="text-2xl font-bold text-[#1A1A1A] font-['Montserrat'] points-display">
                            {stats?.total_points_redeemed?.toLocaleString() || 0}
                        </p>
                    </div>
                    <div className="stats-card" data-testid="active-customers-card">
                        <div className="flex items-center gap-2 text-[#F26B33] mb-2">
                            <Users className="w-4 h-4" />
                            <span className="text-xs font-medium uppercase tracking-wider">Active (30d)</span>
                        </div>
                        <p className="text-2xl font-bold text-[#1A1A1A] font-['Montserrat']">
                            {stats?.active_customers_30d || 0}
                        </p>
                    </div>
                    <div className="stats-card" data-testid="avg-rating-card">
                        <div className="flex items-center gap-2 text-[#329937] mb-2">
                            <Star className="w-4 h-4 fill-current" />
                            <span className="text-xs font-medium uppercase tracking-wider">Avg Rating</span>
                        </div>
                        <p className="text-2xl font-bold text-[#1A1A1A] font-['Montserrat']">
                            {stats?.avg_rating || "N/A"}
                        </p>
                    </div>
                </div>

                {/* Quick Actions */}
                <h2 className="text-lg font-semibold text-[#1A1A1A] mb-3 font-['Montserrat']">Quick Actions</h2>
                <div className="grid grid-cols-2 gap-3 mb-6">
                    <button 
                        onClick={() => navigate("/customers", { state: { openAddModal: true }})}
                        className="quick-action-btn"
                        data-testid="quick-add-customer"
                    >
                        <div className="w-12 h-12 rounded-full bg-[#F26B33]/10 flex items-center justify-center mb-2">
                            <Plus className="w-6 h-6 text-[#F26B33]" />
                        </div>
                        <span className="text-sm font-medium text-[#1A1A1A]">Add Customer</span>
                    </button>
                    <button 
                        onClick={() => navigate("/qr")}
                        className="quick-action-btn"
                        data-testid="quick-qr-code"
                    >
                        <div className="w-12 h-12 rounded-full bg-[#329937]/10 flex items-center justify-center mb-2">
                            <QrCode className="w-6 h-6 text-[#329937]" />
                        </div>
                        <span className="text-sm font-medium text-[#1A1A1A]">Show QR</span>
                    </button>
                </div>

                {/* Recent Customers */}
                <div className="flex items-center justify-between mb-3">
                    <h2 className="text-lg font-semibold text-[#1A1A1A] font-['Montserrat']">Recent Customers</h2>
                    <button 
                        onClick={() => navigate("/customers")}
                        className="text-sm text-[#F26B33] font-medium"
                        data-testid="view-all-customers"
                    >
                        View all
                    </button>
                </div>

                {recentCustomers.length === 0 ? (
                    <div className="empty-state">
                        <Users className="empty-state-icon" />
                        <p className="text-[#52525B]">No customers yet</p>
                        <Button 
                            onClick={() => navigate("/customers", { state: { openAddModal: true }})}
                            className="mt-4 bg-[#F26B33] hover:bg-[#D85A2A] rounded-full"
                            data-testid="add-first-customer"
                        >
                            Add your first customer
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {recentCustomers.map((customer) => (
                            <button
                                key={customer.id}
                                onClick={() => navigate(`/customers/${customer.id}`)}
                                className="customer-list-item w-full text-left"
                                data-testid={`customer-item-${customer.id}`}
                            >
                                <Avatar className="w-10 h-10 mr-3">
                                    <AvatarFallback className="bg-[#329937]/10 text-[#329937] font-semibold">
                                        {customer.name.charAt(0)}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="flex-1 min-w-0">
                                    <p className="font-medium text-[#1A1A1A] truncate">{customer.name} <span className="text-[#52525B] font-normal">({customer.total_visits || 0})</span></p>
                                    <p className="text-sm text-[#52525B]">{customer.phone}</p>
                                </div>
                                <div className="text-right">
                                    <p className="font-semibold text-[#329937] points-display">{customer.total_points}</p>
                                    <Badge variant="outline" className={`tier-badge ${customer.tier.toLowerCase()}`}>
                                        {customer.tier}
                                    </Badge>
                                </div>
                            </button>
                        ))}
                    </div>
                )}
            </div>
        </MobileLayout>
    );
}
