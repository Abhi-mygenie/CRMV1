import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isDemoLoading, setIsDemoLoading] = useState(false);
    const { login, demoLogin } = useAuth();
    const navigate = useNavigate();

    // Load saved credentials on mount
    useEffect(() => {
        const savedEmail = localStorage.getItem("remembered_email");
        const savedPassword = localStorage.getItem("remembered_password");
        if (savedEmail && savedPassword) {
            setEmail(savedEmail);
            setPassword(savedPassword);
            setRememberMe(true);
        }
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            // Save or clear credentials based on remember me
            if (rememberMe) {
                localStorage.setItem("remembered_email", email);
                localStorage.setItem("remembered_password", password);
            } else {
                localStorage.removeItem("remembered_email");
                localStorage.removeItem("remembered_password");
            }
            await login(email, password);
            toast.success("Welcome back!");
            navigate("/");
        } catch (err) {
            toast.error(err.response?.data?.detail || "Login failed");
        } finally {
            setIsLoading(false);
        }
    };

    const handleDemoLogin = async () => {
        setIsDemoLoading(true);
        try {
            await demoLogin();
            toast.success("Welcome to Demo Mode! 🎉");
            navigate("/");
        } catch (err) {
            toast.error(err.response?.data?.detail || "Demo login failed");
        } finally {
            setIsDemoLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#F9F9F7] flex flex-col justify-center p-6">
            <div className="max-w-sm mx-auto w-full">
                <div className="text-center mb-8">
                    <img 
                        src="https://customer-assets.emergentagent.com/job_dine-points-app/artifacts/acdjlx1x_mygenie_logo.svg" 
                        alt="MyGenie Logo" 
                        className="h-20 mx-auto"
                    />
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <Label htmlFor="email" className="form-label">Email</Label>
                        <Input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="owner@restaurant.com"
                            className="h-12 rounded-xl"
                            required
                            data-testid="login-email-input"
                        />
                    </div>
                    <div>
                        <Label htmlFor="password" className="form-label">Password</Label>
                        <div className="relative">
                            <Input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter password"
                                className="h-12 rounded-xl pr-12"
                                required
                                data-testid="login-password-input"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#A1A1AA] hover:text-[#52525B] transition-colors"
                                data-testid="toggle-password-visibility"
                            >
                                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={rememberMe}
                                onChange={(e) => setRememberMe(e.target.checked)}
                                className="w-4 h-4 rounded border-gray-300 text-[#F26B33] focus:ring-[#F26B33]"
                                data-testid="remember-me-checkbox"
                            />
                            <span className="text-sm text-[#52525B]">Remember me</span>
                        </label>
                        <button 
                            type="button"
                            onClick={() => toast.info("Please contact admin to reset your password")}
                            className="text-sm text-[#F26B33] font-medium hover:underline"
                            data-testid="forgot-password-btn"
                        >
                            Forgot password?
                        </button>
                    </div>

                    <Button 
                        type="submit" 
                        className="w-full h-12 rounded-full bg-[#F26B33] hover:bg-[#D85A2A] text-white font-semibold active-scale"
                        disabled={isLoading}
                        data-testid="login-submit-btn"
                    >
                        {isLoading ? "Signing in..." : "Sign In"}
                    </Button>

                    {/* Divider */}
                    <div className="relative my-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-gray-300"></div>
                        </div>
                        <div className="relative flex justify-center text-sm">
                            <span className="px-4 bg-[#F9F9F7] text-[#52525B] font-medium">or</span>
                        </div>
                    </div>

                    {/* Demo Mode Button */}
                    <Button 
                        type="button"
                        onClick={handleDemoLogin}
                        className="w-full h-12 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold active-scale shadow-lg"
                        disabled={isDemoLoading}
                        data-testid="demo-login-btn"
                    >
                        {isDemoLoading ? "Loading Demo..." : "🎭 Try Demo Mode"}
                    </Button>
                    <p className="text-xs text-center text-[#A1A1AA] mt-2">
                        Explore all features with pre-loaded demo data
                    </p>
                    
                    <div className="text-center mt-4">
                        <span className="text-sm text-[#52525B]">Don't have an account? </span>
                        <button 
                            type="button"
                            onClick={() => navigate("/register")}
                            className="text-sm text-[#F26B33] font-medium hover:underline"
                            data-testid="signup-link"
                        >
                            Sign up
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
