import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Avatar, AvatarFallback } from './components/ui/avatar';
import { Separator } from './components/ui/separator';
import { Textarea } from './components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/toaster';
import { 
  MessageSquare, 
  User, 
  School, 
  Clock, 
  Eye, 
  Upload,
  LogOut,
  Plus,
  Search,
  Filter,
  Trophy,
  Crown,
  Award,
  Star,
  Heart,
  BookOpen,
  Users,
  Tag,
  X,
  Calendar,
  Activity,
  Bell,
  Settings,
  Trash2,
  Shield,
  AlertTriangle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://unisoruyorsonhali-production.up.railway.app';
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      const userData = localStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
      }
    }
    setLoading(false);
  }, [token]);

  const login = (tokenData) => {
    localStorage.setItem('token', tokenData.access_token);
    localStorage.setItem('user', JSON.stringify(tokenData.user));
    setToken(tokenData.access_token);
    setUser(tokenData.user);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    login,
    logout,
    loading,
    setUser
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Login Component
const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    username: '',
    university: '',
    faculty: '',
    department: '',
    isYKSStudent: false
  });
  const [universities, setUniversities] = useState([]);
  const [faculties, setFaculties] = useState([]);
  const [universitySearch, setUniversitySearch] = useState('');
  const [facultySearch, setFacultySearch] = useState('');
  const [showUniversityDropdown, setShowUniversityDropdown] = useState(false);
  const [showFacultyDropdown, setShowFacultyDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  const { user } = useAuth();
  useEffect(() => {
    if (user) {
      navigate('/', { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    if (!isLogin) {
      fetchUniversities();
      fetchFaculties();
    } else {
      // Reset search values when switching to login mode
      setUniversitySearch('');
      setFacultySearch('');
      setShowUniversityDropdown(false);
      setShowFacultyDropdown(false);
    }
  }, [isLogin]);

  // Sync search values with formData
  useEffect(() => {
    if (formData.university && formData.university !== universitySearch) {
      setUniversitySearch(formData.university);
    }
    if (formData.faculty && formData.faculty !== facultySearch) {
      setFacultySearch(formData.faculty);
    }
  }, [formData.university, formData.faculty]);

  const fetchUniversities = async () => {
    try {
      const response = await axios.get(`${API}/universities`);
      setUniversities(response.data.universities);
    } catch (err) {
      console.error('Üniversiteler yüklenemedi:', err);
    }
  };

  const fetchFaculties = async () => {
    try {
      const response = await axios.get(`${API}/faculties`);
      setFaculties(response.data.faculties);
    } catch (err) {
      console.error('Fakülteler yüklenemedi:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Kayıt olurken şifre kontrolü
    if (!isLogin) {
      if (formData.password !== formData.confirmPassword) {
        setError('Şifreler uyuşmuyor. Lütfen aynı şifreyi iki kez girin.');
        setLoading(false);
        return;
      }
      if (formData.password.length < 6) {
        setError('Şifre en az 6 karakter olmalıdır.');
        setLoading(false);
        return;
      }
    }

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = isLogin 
        ? { email_or_username: formData.email, password: formData.password }
        : formData;

      const response = await axios.post(`${API}${endpoint}`, payload);
      login(response.data);
      navigate('/', { replace: true }); // Replace history to prevent back button issues
    } catch (err) {
      // Handle profanity error in registration
      if (err.response && err.response.status === 400 && err.response.data.detail && err.response.data.detail.includes('uygunsuz kelime')) {
        setError(err.response.data.detail);
        toast.error(err.response.data.detail, {
          duration: 5000
        });
      } else {
        setError(err.response?.data?.detail || 'Bir hata oluştu');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear error when user starts typing
    if (error) setError('');
  };

  const toggleLoginMode = () => {
    setIsLogin(!isLogin);
    // Reset form data when switching modes
    setFormData({
      email: '',
      password: '',
      confirmPassword: '',
      username: '',
      university: '',
      faculty: '',
      department: '',
      isYKSStudent: false
    });
    // Reset search values
    setUniversitySearch('');
    setFacultySearch('');
    setShowUniversityDropdown(false);
    setShowFacultyDropdown(false);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-orange-100 to-orange-200 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl border border-orange-100 bg-white backdrop-blur-sm">
        <CardHeader className="text-center space-y-3 pb-4">
          <div className="cursor-pointer" onClick={() => navigate('/')}>
            <img 
              src="https://customer-assets.emergentagent.com/job_student-forum-1/artifacts/0f9o2m08_ChatGPT%20Image%205%20Eyl%202025%2021_49_28.png" 
              alt="unisoruyor.com logo" 
              className="w-16 h-16 object-contain mx-auto hover:opacity-80 transition-opacity"
            />
            <h2 className="text-lg font-bold text-orange-600 hover:text-orange-700 transition-colors mt-2">
              Üniversiteliler Soruyor
            </h2>
          </div>
          <div className="w-16 h-0.5 bg-gradient-to-r from-orange-400 to-orange-600 mx-auto"></div>
          <CardTitle className="text-xl font-semibold text-gray-800">
            {isLogin ? 'Hesabına Giriş Yap' : 'Yeni Hesap Oluştur'}
          </CardTitle>
          {!isLogin && (
            <p className="text-sm text-gray-600">
              Binlerce öğrenci topluluğuna katıl
            </p>
          )}
        </CardHeader>
        <CardContent className="px-6 pb-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLogin && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="username">Kullanıcı Adı</Label>
                  <Input
                    id="username"
                    name="username"
                    required
                    value={formData.username}
                    onChange={handleChange}
                    placeholder="Kullanıcı adınızı girin"
                    className="border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                  />
                </div>
                
                {/* YKS Student Checkbox */}
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="isYKSStudent"
                    checked={formData.isYKSStudent}
                    onChange={(e) => setFormData(prev => ({ 
                      ...prev, 
                      isYKSStudent: e.target.checked,
                      // Clear university fields when YKS is selected
                      university: e.target.checked ? '' : prev.university,
                      faculty: e.target.checked ? '' : prev.faculty,
                      department: e.target.checked ? '' : prev.department
                    }))}
                    className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                  />
                  <Label htmlFor="isYKSStudent" className="text-sm font-medium text-gray-700 cursor-pointer">
                    YKS öğrencisiyim (Henüz üniversite tercihimi yapmadım)
                  </Label>
                </div>
                
                {/* University fields - only show if not YKS student */}
                {!formData.isYKSStudent && (
                <>
                <div className="space-y-2">
                  <Label htmlFor="university">Üniversite</Label>
                  <div className="relative">
                    <Input
                      type="text"
                      placeholder="Üniversitenizi arayın..."
                      value={universitySearch}
                      onChange={(e) => {
                        const value = e.target.value;
                        setUniversitySearch(value);
                        setShowUniversityDropdown(true);
                        
                        // Clear formData.university if the typed value doesn't match exactly
                        if (!universities.includes(value)) {
                          setFormData({ ...formData, university: '' });
                        } else {
                          setFormData({ ...formData, university: value });
                        }
                      }}
                      onFocus={() => setShowUniversityDropdown(true)}
                      className="border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                      required
                    />
                    {universitySearch && (
                      <button
                        type="button"
                        onClick={() => {
                          setUniversitySearch('');
                          setFormData({ ...formData, university: '' });
                        }}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                    
                    {/* University Dropdown */}
                    {showUniversityDropdown && universitySearch && (
                      <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                        {universities
                          .filter(uni => {
                            // Turkish character normalization for search
                            const normalizeText = (text) => {
                              return text.toLowerCase()
                                .replace(/İ/g, 'i')  // Capital İ first
                                .replace(/I/g, 'ı')  // Capital I to ı
                                .replace(/i̇/g, 'i')  // Dotted i to normal i (CRITICAL FIX!)
                                .replace(/ğ/gi, 'g')
                                .replace(/ü/gi, 'u')
                                .replace(/ş/gi, 's')
                                .replace(/ı/g, 'i')  // ı to i
                                .replace(/ö/gi, 'o')
                                .replace(/ç/gi, 'c');
                            };
                            
                            const normalizedUni = normalizeText(uni);
                            const normalizedSearch = normalizeText(universitySearch);
                            
                            // Debug log
                            if (universitySearch.toLowerCase().includes('istanbul')) {
                              console.log(`Searching: "${universitySearch}" → "${normalizedSearch}"`);
                              console.log(`University: "${uni}" → "${normalizedUni}"`);
                              console.log(`Match: ${normalizedUni.includes(normalizedSearch)}`);
                            }
                            
                            return normalizedUni.includes(normalizedSearch);
                          })
                          .slice(0, 10)
                          .map((university, index) => (
                            <button
                              key={index}
                              type="button"
                              onClick={() => {
                                setFormData({ ...formData, university: university });
                                setUniversitySearch(university);
                                setShowUniversityDropdown(false);
                              }}
                              className="w-full text-left px-3 py-2 hover:bg-orange-50 focus:bg-orange-50 focus:outline-none text-sm"
                            >
                              {university}
                            </button>
                          ))}
                        
                        {universities.filter(uni => {
                          const normalizeText = (text) => {
                            return text.toLowerCase()
                              .replace(/ğ/g, 'g')
                              .replace(/ü/g, 'u')
                              .replace(/ş/g, 's')
                              .replace(/ı/g, 'i')
                              .replace(/ö/g, 'o')
                              .replace(/ç/g, 'c')
                              .replace(/İ/g, 'i')
                              .replace(/Ğ/g, 'g')
                              .replace(/Ü/g, 'u')
                              .replace(/Ş/g, 's')
                              .replace(/Ö/g, 'o')
                              .replace(/Ç/g, 'c');
                          };
                          const normalizedUni = normalizeText(uni);
                          const normalizedSearch = normalizeText(universitySearch);
                          return normalizedUni.includes(normalizedSearch);
                        }).length === 0 && (
                          <div className="px-3 py-2 text-sm text-gray-500">
                            Sonuç bulunamadı
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="faculty">Fakülte</Label>
                  <div className="relative">
                    <Input
                      type="text"
                      placeholder="Fakültenizi arayın..."
                      value={facultySearch}
                      onChange={(e) => {
                        const value = e.target.value;
                        setFacultySearch(value);
                        setShowFacultyDropdown(true);
                        
                        // Clear formData.faculty if the typed value doesn't match exactly
                        if (!faculties.includes(value)) {
                          setFormData({ ...formData, faculty: '' });
                        } else {
                          setFormData({ ...formData, faculty: value });
                        }
                      }}
                      onFocus={() => setShowFacultyDropdown(true)}
                      className="border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                      required
                    />
                    {facultySearch && (
                      <button
                        type="button"
                        onClick={() => {
                          setFacultySearch('');
                          setFormData({ ...formData, faculty: '' });
                        }}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                    
                    {/* Faculty Dropdown */}
                    {showFacultyDropdown && facultySearch && (
                      <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                        {faculties
                          .filter(fac => fac.toLowerCase().includes(facultySearch.toLowerCase()))
                          .slice(0, 10)
                          .map((faculty, index) => (
                            <button
                              key={index}
                              type="button"
                              onClick={() => {
                                setFormData({ ...formData, faculty: faculty });
                                setFacultySearch(faculty);
                                setShowFacultyDropdown(false);
                              }}
                              className="w-full text-left px-3 py-2 hover:bg-orange-50 focus:bg-orange-50 focus:outline-none text-sm"
                            >
                              {faculty}
                            </button>
                          ))}
                        
                        {faculties.filter(fac => fac.toLowerCase().includes(facultySearch.toLowerCase())).length === 0 && (
                          <div className="px-3 py-2 text-sm text-gray-500">
                            Sonuç bulunamadı
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="department">Bölüm</Label>
                  <Input
                    id="department"
                    name="department"
                    required
                    value={formData.department}
                    onChange={handleChange}
                    className="border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                    placeholder="Örn: Bilgisayar Mühendisliği"
                  />
                </div>
                </>
                )}
              </>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="email">{isLogin ? 'Mail Adresi veya Kullanıcı Adı' : 'Mail Adresi'}</Label>
              <Input
                id="email"
                name="email"
                type={isLogin ? "text" : "email"}
                required
                value={formData.email}
                onChange={handleChange}
                className="border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                placeholder={isLogin ? "Mail adresiniz veya kullanıcı adınız" : "Mail adresinizi girin"}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Şifre</Label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                placeholder="Şifrenizi girin"
                className="border-gray-300 focus:border-orange-500 focus:ring-orange-500"
              />
            </div>

            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Şifre Tekrarı</Label>
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  required
                  value={formData.confirmPassword || ''}
                  onChange={handleChange}
                  placeholder="Şifrenizi tekrar girin"
                  className="border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                />
                {formData.confirmPassword && formData.password !== formData.confirmPassword && (
                  <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    Şifreler uyuşmuyor
                  </p>
                )}
                {formData.confirmPassword && formData.password === formData.confirmPassword && formData.password.length > 0 && (
                  <p className="text-green-500 text-xs mt-1 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Şifreler uyuşuyor
                  </p>
                )}
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
                <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white shadow-lg"
              disabled={loading}
            >
              {loading ? 'Yükleniyor...' : (isLogin ? 'Giriş Yap' : 'Kayıt Ol')}
            </Button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={toggleLoginMode}
                className="text-orange-600 hover:text-orange-700 text-sm font-medium transition-colors relative group"
              >
                {isLogin ? 'Hesabınız yok mu? Kayıt olun' : 'Zaten hesabınız var mı? Giriş yapın'}
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-600 group-hover:w-full transition-all duration-300"></span>
              </button>
            </div>
          </form>

          {/* Click outside to close dropdowns */}
          {showUniversityDropdown && (
            <div
              className="fixed inset-0 z-40"
              onClick={() => setShowUniversityDropdown(false)}
            />
          )}
          {showFacultyDropdown && (
            <div
              className="fixed inset-0 z-40"
              onClick={() => setShowFacultyDropdown(false)}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// User Profile Modal Component
const UserProfileModal = ({ userId, username, onClose }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user: currentUser } = useAuth(); // Get current user for admin check

  useEffect(() => {
    if (userId) {
      fetchUserProfile();
    }
  }, [userId]);

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get(`${API}/users/${userId}/profile`);
      setProfile(response.data);
    } catch (err) {
      console.error('Profil yüklenirken hata:', err);
    } finally {
      setLoading(false);
    }
  };

  // Admin functions
  const handleMakeAdmin = async () => {
    if (window.confirm(`${username} kullanıcısına admin yetkisi vermek istediğinizden emin misiniz?`)) {
      try {
        await axios.post(`${API}/admin/make-admin/${userId}`, {}, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        alert(`${username} kullanıcısı admin yapıldı`);
        fetchUserProfile(); // Refresh profile
      } catch (err) {
        alert('Hata: ' + (err.response?.data?.detail || 'Admin yapma işlemi başarısız'));
      }
    }
  };

  const handleBanUser = async () => {
    if (window.confirm(`${username} kullanıcısını yasaklamak istediğinizden emin misiniz? Bu kullanıcının hesabı kalıcı olarak silinecektir!`)) {
      if (window.confirm('SON UYARI: Bu işlem geri alınamaz. Kullanıcı hesabı tamamen silinecek. Emin misiniz?')) {
        try {
          await axios.post(`${API}/admin/ban-user/${userId}`, {}, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          });
          alert(`${username} kullanıcısı yasaklandı ve hesabı silindi`);
          onClose(); // Close modal since user is deleted
        } catch (err) {
          alert('Hata: ' + (err.response?.data?.detail || 'Yasaklama işlemi başarısız'));
        }
      }
    }
  };

  const handleMuteUser = async () => {
    const hours = prompt(`${username} kullanıcısını kaç saat susturmak istiyorsunuz?`, '24');
    if (!hours || isNaN(hours) || hours < 1) {
      alert('Lütfen geçerli bir saat sayısı girin');
      return;
    }

    try {
      await axios.post(`${API}/admin/mute-user/${userId}`, {
        mute_hours: parseInt(hours)
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      alert(`${username} kullanıcısı ${hours} saat susturuldu`);
      fetchUserProfile(); // Refresh profile
    } catch (err) {
      alert('Hata: ' + (err.response?.data?.detail || 'Susturma işlemi başarısız'));
    }
  };

  const handleWarnUser = async () => {
    const message = prompt(`${username} kullanıcısına göndermek istediğiniz uyarı mesajını yazın:`, '');
    if (!message || message.trim() === '') {
      alert('Lütfen bir uyarı mesajı yazın');
      return;
    }

    try {
      await axios.post(`${API}/admin/warn-user/${userId}`, {
        warning_message: message.trim()
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      alert(`${username} kullanıcısına uyarı gönderildi`);
    } catch (err) {
      alert('Hata: ' + (err.response?.data?.detail || 'Uyarı gönderme işlemi başarısız'));
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Europe/Istanbul'
    });
  };

  if (loading) {
    return (
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        onClick={onClose} // Backdrop click to close
      >
        <div 
          className="bg-white rounded-lg p-6 max-w-2xl w-full m-4"
          onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
        >
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2 mb-6"></div>
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        onClick={onClose} // Backdrop click to close
      >
        <div 
          className="bg-white rounded-lg p-6 max-w-2xl w-full m-4"
          onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
        >
          <div className="text-center">
            <p className="text-red-600">Profil yüklenemedi</p>
            <Button onClick={onClose} className="mt-4">Kapat</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={onClose} // Backdrop click to close
    >
      <div 
        className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="bg-gradient-to-br from-orange-500 to-orange-600 text-white text-xl">
                {profile.user.username.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{profile.user.username}</h2>
              <div className="space-y-1 mt-2">
                <div className="flex items-center gap-2 text-gray-600">
                  <School className="h-4 w-4" />
                  <span>{profile.user.university}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                  <span>🏛️ {profile.user.faculty}</span>
                  <span>•</span>
                  <span>🎓 {profile.user.department}</span>
                </div>
              </div>
              <div className="flex items-center gap-2 text-gray-500 text-sm mt-1">
                <Calendar className="h-3 w-3" />
                <span>Katılım: {formatDate(profile.user.created_at)}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Admin Buttons - Only visible to admins and not for themselves */}
            {currentUser?.is_admin && currentUser.id !== userId && (
              <div className="flex gap-2 mr-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleMakeAdmin}
                  className="border-green-300 text-green-600 hover:bg-green-50 text-xs px-3"
                >
                  👑 YETKİ
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBanUser}
                  className="border-red-500 text-red-700 hover:bg-red-50 text-xs px-3"
                >
                  🚫 YASAKLA
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleMuteUser}
                  className="border-yellow-500 text-yellow-700 hover:bg-yellow-50 text-xs px-3"
                >
                  🔇 SUSTUR
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleWarnUser}
                  className="border-orange-500 text-orange-700 hover:bg-orange-50 text-xs px-3"
                >
                  ⚠️ UYAR
                </Button>
              </div>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="border-gray-300"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="h-5 w-5 text-orange-500" />
            Aktivite İstatistikleri
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-orange-600">{profile.stats.question_count}</div>
                <div className="text-sm text-gray-500">Soru</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-600">{profile.stats.answer_count}</div>
                <div className="text-sm text-gray-500">Cevap</div>
              </CardContent>
            </Card>

          </div>
        </div>

        {/* Recent Activity */}
        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Questions */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-orange-500" />
              Son Sorular ({profile.recent_questions.length})
            </h3>
            <div className="space-y-3">
              {profile.recent_questions.length === 0 ? (
                <p className="text-gray-500 text-sm">Henüz soru yok</p>
              ) : (
                profile.recent_questions.map((question) => (
                  <Card key={question.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <h4 className="font-medium text-sm mb-2 line-clamp-2">{question.title}</h4>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <Badge variant="secondary" className="text-xs">{question.category}</Badge>
                        <div className="flex items-center gap-2">
                          <span>{question.answer_count} cevap</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>

          {/* Recent Answers */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <User className="h-5 w-5 text-green-500" />
              Son Cevaplar ({profile.recent_answers.length})
            </h3>
            <div className="space-y-3">
              {profile.recent_answers.length === 0 ? (
                <p className="text-gray-500 text-sm">Henüz cevap yok</p>
              ) : (
                profile.recent_answers.map((answer) => (
                  <Card key={answer.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <h4 className="font-medium text-sm mb-2 line-clamp-1">{answer.question_title}</h4>
                      <p className="text-xs text-gray-600 mb-2 line-clamp-2">{answer.content}</p>
                      <div className="text-xs text-gray-500">
                        {formatDate(answer.created_at)}
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Category Filter Component with Search and Grid Layout
const CategoryFilter = ({ selectedCategory, onCategoryChange, categories }) => {
  const [expandedCategory, setExpandedCategory] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAllCategories, setShowAllCategories] = useState(false); // New state

  // Priority categories to show first
  const priorityCategories = ['Mühendislik Fakültesi', 'Tıp Fakültesi', 'YKS', 'KYK Yurtları', 'Dersler', 'Burslar'];

  const handleMainCategoryClick = (mainCategory) => {
    if (expandedCategory === mainCategory) {
      setExpandedCategory(null);
    } else {
      setExpandedCategory(mainCategory);
    }
  };

  // Category icons mapping
  const getCategoryIcon = (categoryName) => {
    const iconMap = {
      'Mühendislik Fakültesi': '⚙️',
      'Tıp Fakültesi': '🏥',
      'Fen-Edebiyat Fakültesi': '📚',
      'İktisadi ve İdari Bilimler Fakültesi': '💼',
      'Hukuk Fakültesi': '⚖️',
      'Eğitim Fakültesi': '🎓',
      'Güzel Sanatlar Fakültesi': '🎨',
      'Mimarlık Fakültesi': '🏗️',
      'Ziraat Fakültesi': '🌱',
      'İletişim Fakültesi': '📺',
      'Spor Bilimleri Fakültesi': '⚽',
      'KYK Yurtları': '🏠',
      'Burslar': '💰',
      'YKS': '📝',
      'Diğer': '❓'
    };
    return iconMap[categoryName] || '📂';
  };

  // Filter categories based on search term
  const filterCategories = (categories) => {
    if (!searchTerm || !categories || typeof categories !== 'object') return categories || {};
    
    const filtered = {};
    Object.keys(categories).forEach(mainCategory => {
      const filteredSubCategories = categories[mainCategory].filter(subCategory =>
        subCategory.toLowerCase().includes(searchTerm.toLowerCase()) ||
        mainCategory.toLowerCase().includes(searchTerm.toLowerCase())
      );
      
      if (filteredSubCategories.length > 0 || 
          mainCategory.toLowerCase().includes(searchTerm.toLowerCase())) {
        filtered[mainCategory] = categories[mainCategory];
      }
    });
    return filtered;
  };

  const filteredCategories = filterCategories(categories);
  
  // Get categories to display based on showAllCategories state
  const getCategoriesToShow = () => {
    const allCategories = Object.keys(filteredCategories || {});
    
    if (searchTerm) {
      // If searching, show all filtered results
      return allCategories;
    }
    
    if (showAllCategories) {
      // If showing all, return all categories
      return allCategories;
    } else {
      // If not showing all, prioritize and limit to first 6
      const priority = allCategories.filter(cat => priorityCategories.includes(cat));
      const others = allCategories.filter(cat => !priorityCategories.includes(cat));
      return [...priority, ...others].slice(0, 6);
    }
  };

  const categoriesToShow = getCategoriesToShow();
  const hasMoreCategories = Object.keys(filteredCategories || {}).length > 6;

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <Tag className="h-5 w-5 text-orange-500" />
        <h3 className="font-semibold text-gray-900">Kategoriler</h3>
      </div>
      
      {/* Search Input */}
      <div className="mb-4">
        <div className="relative">
          <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <Input
            type="text"
            placeholder="Kategori ara..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 border-orange-300 focus:border-orange-500 focus:ring-orange-500"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
      
      <div className="space-y-3">
        {/* All button */}
        <div>
          <Button
            variant={selectedCategory === '' ? 'default' : 'outline'}
            size="sm"
            onClick={() => onCategoryChange('')}
            className={selectedCategory === '' 
              ? 'bg-orange-500 hover:bg-orange-600' 
              : 'border-orange-300 text-orange-600 hover:bg-orange-50'
            }
          >
            🏠 Tüm Sorular
          </Button>
        </div>

        {/* Main Categories - Grid Layout */}
        <div className="grid grid-cols-2 gap-3">
          {categoriesToShow.map((mainCategory) => (
            <div key={mainCategory} className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleMainCategoryClick(mainCategory)}
                className="w-full justify-start border-orange-300 text-orange-700 hover:bg-orange-50 flex items-center gap-2"
              >
                <span className="text-lg">{getCategoryIcon(mainCategory)}</span>
                <span className="text-xs flex-1 truncate">{mainCategory}</span>
                <span className="text-xs">({categories[mainCategory]?.length || 0})</span>
              </Button>
              
              {/* Subcategories - 2 Column Layout */}
              {expandedCategory === mainCategory && (
                <div className="ml-2 grid grid-cols-2 gap-1">
                  {categories[mainCategory]
                    ?.filter(subCategory => 
                      !searchTerm || 
                      subCategory.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      mainCategory.toLowerCase().includes(searchTerm.toLowerCase())
                    )
                    .map((subCategory) => (
                      <Button
                        key={`${mainCategory}-${subCategory}`}
                        variant={selectedCategory === subCategory ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => onCategoryChange(subCategory)}
                        className={selectedCategory === subCategory
                          ? 'bg-orange-500 hover:bg-orange-600 text-white text-xs px-2 py-1 h-auto justify-start'
                          : 'border-orange-200 text-orange-600 hover:bg-orange-50 text-xs px-2 py-1 h-auto justify-start'
                        }
                      >
                        <span className="truncate text-left">{subCategory}</span>
                      </Button>
                    ))
                  }
                </div>
              )}
            </div>
          ))}
        </div>
        
        {/* Show All Categories Button */}
        {!searchTerm && hasMoreCategories && (
          <div className="text-center mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAllCategories(!showAllCategories)}
              className="border-orange-300 text-orange-600 hover:bg-orange-50"
            >
              {showAllCategories ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-1" />
                  Daha az göster
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-1" />
                  Tüm kategorileri görüntüle ({Object.keys(filteredCategories || {}).length - 6} daha)
                </>
              )}
            </Button>
          </div>
        )}
      </div>

      {/* No results message */}
      {searchTerm && Object.keys(filteredCategories || {}).length === 0 && (
        <div className="text-center py-4 text-gray-500">
          <Search className="h-8 w-8 mx-auto mb-2 text-gray-300" />
          <p className="text-sm">Arama sonucu bulunamadı</p>
        </div>
      )}
    </div>
  );
};

// Question Form Component with Search and File Upload
const QuestionForm = ({ onQuestionCreated }) => {
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: ''
  });
  const [categories, setCategories] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [categorySearch, setCategorySearch] = useState('');
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploadLoading, setUploadLoading] = useState(false);
  const { token, user } = useAuth();
  const { toast } = useToast();

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories`);
      setCategories(response.data);
    } catch (err) {
      console.error('Kategori yükleme hatası:', err);
    }
  };

  const handleFileUpload = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    setUploadLoading(true);
    
    try {
      for (let file of files) {
        // Check file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
          alert(`${file.name} dosyası 10MB'den büyük. Lütfen daha küçük bir dosya seçin.`);
          continue;
        }
        
        // Check file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
        if (!allowedTypes.includes(file.type)) {
          alert(`${file.name} desteklenmeyen dosya formatı. Sadece PNG, JPG, GIF, WebP ve PDF dosyaları yüklenebilir.`);
          continue;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(`${API}/files/upload`, formData, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        
        setUploadedFiles(prev => [...prev, {
          id: response.data.file_id,
          name: file.name,
          size: file.size,
          type: file.type
        }]);
      }
    } catch (err) {
      console.error('Dosya yükleme hatası:', err);
      alert('Dosya yükleme sırasında bir hata oluştu');
    } finally {
      setUploadLoading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Form validasyonları
    if (!formData.title || formData.title.trim().length < 5) {
      setError('Soru başlığı en az 5 karakter olmalıdır.');
      return;
    }
    
    if (!formData.content || formData.content.trim().length < 4) {
      setError('Soru içeriği en az 4 karakter olmalıdır.');
      return;
    }
    
    if (!formData.category) {
      setError('Lütfen bir kategori seçin.');
      return;
    }
    
    setLoading(true);

    try {
      const questionData = {
        ...formData,
        attachments: uploadedFiles.map(file => file.id)
      };
      
      const response = await axios.post(`${API}/questions`, questionData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      onQuestionCreated(response.data);
      setFormData({ title: '', content: '', category: '' });
      setCategorySearch('');
      setUploadedFiles([]);
      setShowForm(false);
      
      // Başarı toastı göster
      toast({
        title: "✅ Başarılı!",
        description: "Sorunuz başarıyla paylaşıldı.",
        variant: "success"
      });
    } catch (err) {
      console.error('Soru oluşturma hatası:', err);
      
      // Handle profanity error
      if (err.response && err.response.status === 400 && err.response.data.detail && err.response.data.detail.includes('uygunsuz kelime')) {
        setError(err.response.data.detail);
        toast.error(err.response.data.detail, {
          duration: 5000
        });
      }
      // Handle rate limiting error
      else if (err.response && err.response.status === 429) {
        setError(err.response.data.detail || 'Çok sık soru soruyorsunuz. Lütfen bekleyip tekrar deneyin.');
      } else {
        setError('Soru oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear error when user starts typing
    if (error) setError('');
  };

  // Get all subcategories for search
  const getAllSubCategories = () => {
    const allCategories = [];
    if (categories && typeof categories === 'object') {
      Object.keys(categories).forEach(mainCategory => {
        categories[mainCategory].forEach(subCategory => {
          allCategories.push({
            value: subCategory,
            label: `${subCategory} (${mainCategory})`,
            mainCategory: mainCategory,
            icon: getCategoryIcon(mainCategory)
          });
        });
      });
    }
    return allCategories;
  };

  // Category icons helper
  const getCategoryIcon = (categoryName) => {
    const iconMap = {
      'Mühendislik Fakültesi': '⚙️',
      'Tıp Fakültesi': '🏥',
      'Fen-Edebiyat Fakültesi': '📚',
      'İktisadi ve İdari Bilimler Fakültesi': '💼',
      'Hukuk Fakültesi': '⚖️',
      'Eğitim Fakültesi': '🎓',
      'Güzel Sanatlar Fakültesi': '🎨',
      'Mimarlık Fakültesi': '🏗️',
      'Ziraat Fakültesi': '🌱',
      'İletişim Fakültesi': '📺',
      'Spor Bilimleri Fakültesi': '⚽',
      'KYK Yurtları': '🏠',
      'Burslar': '💰',
      'YKS': '📝',
      'Diğer': '❓'
    };
    return iconMap[categoryName] || '📂';
  };

  // Filter categories based on search
  const filteredCategories = getAllSubCategories().filter(cat =>
    cat.label.toLowerCase().includes(categorySearch.toLowerCase())
  );

  const handleCategorySelect = (category) => {
    console.log('Kategori seçildi:', category);
    setFormData({ ...formData, category: category.value });
    setCategorySearch(category.label);
    setShowCategoryDropdown(false);
    console.log('Form data güncellendi, category:', category.value);
  };

  if (!showForm) {
    return (
      <Button
        onClick={() => setShowForm(true)}
        className="mb-6 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white shadow-lg"
      >
        <Plus className="h-4 w-4 mr-2" />
        Yeni Soru Sor
      </Button>
    );
  }

  return (
    <Card className="mb-6 shadow-lg border-orange-200">
      <CardHeader>
        <CardTitle className="text-xl text-gray-900">Yeni Soru Sor</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Başlık</Label>
            <Input
              id="title"
              name="title"
              required
              value={formData.title}
              onChange={handleChange}
              className="border-gray-300 focus:border-orange-500 focus:ring-orange-500"
              placeholder="Sorunuzun başlığını yazın..."
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="content">İçerik</Label>
            <Textarea
              id="content"
              name="content"
              required
              value={formData.content}
              onChange={handleChange}
              className="border-gray-300 focus:border-orange-500 focus:ring-orange-500 min-h-[120px]"
              placeholder="Sorunuzun detaylarını yazın..."
            />
          </div>

          <div className="space-y-4">
            {/* Category Typeahead */}
            <div className="space-y-2 relative">
              <Label>Kategori Yaz ve Seç *</Label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Kategori adı yazın (en az 2 harf)..."
                  value={categorySearch}
                  onChange={(e) => {
                    const value = e.target.value;
                    setCategorySearch(value);
                    // Show dropdown only if 2 or more characters
                    setShowCategoryDropdown(value.length >= 2);
                  }}
                  onFocus={() => {
                    // Show dropdown only if there are 2+ characters
                    if (categorySearch.length >= 2) {
                      setShowCategoryDropdown(true);
                    }
                  }}
                  onBlur={() => {
                    // Delay hiding dropdown to allow clicks
                    setTimeout(() => setShowCategoryDropdown(false), 150);
                  }}
                  className="w-full px-3 py-2 border border-orange-200 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
                <Search className="absolute right-3 top-3 h-4 w-4 text-gray-400" />
                
                {/* Typeahead Dropdown */}
                {showCategoryDropdown && categorySearch.length >= 2 && (
                  <div className="absolute z-50 w-full mt-1 bg-white border border-orange-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
                    {filteredCategories.length === 0 ? (
                      <div className="px-3 py-2 text-sm text-gray-500 text-center">
                        Eşleşen kategori bulunamadı
                      </div>
                    ) : (
                      <>
                        {filteredCategories.slice(0, 15).map((category, index) => (
                          <button
                            key={index}
                            type="button"
                            className="w-full px-3 py-2 text-left hover:bg-orange-50 flex items-center gap-2 transition-colors"
                            onClick={() => handleCategorySelect(category)}
                          >
                            <span className="text-lg">{category.icon}</span>
                            <div className="flex-1">
                              <span className="font-medium text-orange-600">
                                {category.value}
                              </span>
                              <span className="text-gray-500 text-xs ml-2">
                                ({category.mainCategory})
                              </span>
                            </div>
                          </button>
                        ))}
                        {filteredCategories.length > 15 && (
                          <div className="px-3 py-2 text-xs text-gray-500 border-t bg-gray-50">
                            İlk 15 sonuç gösteriliyor. Daha spesifik yazın...
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
                
                {/* Selected Category Display */}
                {formData.category && (
                  <div className="mt-2 p-2 bg-orange-50 border border-orange-200 rounded-md flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {getCategoryIcon(getAllSubCategories().find(cat => cat.value === formData.category)?.mainCategory)}
                      </span>
                      <span className="text-sm font-medium text-orange-700">
                        Seçili: {formData.category}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setFormData({ ...formData, category: '' });
                        setCategorySearch('');
                      }}
                      className="text-orange-600 hover:text-orange-800 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* File Upload Section */}
            <div className="space-y-2">
              <Label>Dosya Ekle (İsteğe Bağlı)</Label>
              <div className="border-2 border-dashed border-orange-300 rounded-lg p-4 hover:border-orange-400 transition-colors">
                <input
                  type="file"
                  multiple
                  accept=".png,.jpg,.jpeg,.gif,.webp,.pdf"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                  disabled={uploadLoading}
                />
                <label 
                  htmlFor="file-upload" 
                  className="cursor-pointer flex flex-col items-center gap-2 text-center"
                >
                  <Upload className="h-8 w-8 text-orange-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-700">
                      {uploadLoading ? 'Yükleniyor...' : 'Dosya seç veya buraya sürükle'}
                    </p>
                    <p className="text-xs text-gray-500">
                      PNG, JPG, GIF, WebP, PDF (Maks 10MB)
                    </p>
                  </div>
                </label>
              </div>
              
              {/* Uploaded Files */}
              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-medium text-gray-700">Yüklenen Dosyalar:</p>
                  {uploadedFiles.map((file) => (
                    <div key={file.id} className="flex items-center justify-between p-2 bg-orange-50 rounded-md">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm text-gray-700">{file.name}</span>
                        <span className="text-xs text-gray-500">({formatFileSize(file.size)})</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(file.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <User className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">Profil Bilgilerin:</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs text-blue-700">
                <div>📚 {user?.university}</div>
                <div>🏛️ {user?.faculty}</div>
                <div>🎓 {user?.department}</div>
              </div>
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center bg-red-50 p-2 rounded mb-4">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <Button 
              type="submit" 
              disabled={loading || !formData.category || uploadLoading}
              className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white"
            >
              {loading ? 'Gönderiliyor...' : 'Soruyu Gönder'}
            </Button>
            <Button 
              type="button"
              variant="outline"
              onClick={() => {
                setShowForm(false);
                setCategorySearch('');
                setUploadedFiles([]);
                setFormData({ title: '', content: '', category: '' });
              }}
              className="border-orange-300 text-orange-600 hover:bg-orange-50"
            >
              İptal
            </Button>
          </div>
        </form>

        {/* Click outside to close dropdown */}
        {showCategoryDropdown && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowCategoryDropdown(false)}
          />
        )}
      </CardContent>
    </Card>
  );
};

// Question Card Component
const QuestionCard = ({ question, onClick, user, onUserClick, onCategoryClick }) => {
  const { user: authUser } = useAuth(); // AuthContext'ten user al
  const currentUser = user || authUser; // Prop'dan veya context'ten user kullan
  const handleDelete = async (e) => {
    e.stopPropagation();
    
    if (!window.confirm('Bu soruyu silmek istediğinizden emin misiniz?')) return;
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        alert('Lütfen giriş yapın');
        return;
      }
      
      await axios.delete(`${API}/questions/${question.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Soru silindi!');
      window.location.reload();
      
    } catch (err) {
      console.error('Delete error:', err);
      if (err.response?.status === 401 || err.response?.status === 403) {
        alert('Oturum süresi dolmuş olabilir. Lütfen çıkış yapıp tekrar giriş yapın.');
        // Clear localStorage and redirect to login
        localStorage.clear();
        window.location.href = '/login';
      } else {
        alert('Hata: ' + (err.response?.data?.detail || 'Silme işlemi başarısız'));
      }
    }
  };

  const canDelete = currentUser && (currentUser.id === question.author_id || currentUser.is_admin);

  return (
    <Card 
      className="question-card hover:shadow-xl transition-all duration-200 cursor-pointer border-l-4 border-l-orange-500"
      onClick={() => onClick(question)}
    >
      <CardContent className="card-content">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 line-clamp-2">
              {question.title}
            </h3>
            <p className="text-gray-600 line-clamp-2">
              {question.content}
            </p>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-1 badges">
          <Badge 
            style={{
              backgroundColor: '#fed7aa',
              color: '#9a3412',
              border: '1px solid #fb923c'
            }}
            className="text-xs px-2 py-0.5 cursor-pointer hover:bg-orange-200 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              onCategoryClick && onCategoryClick(question.category);
            }}
          >
            {question.category}
          </Badge>
          <Badge variant="outline" className="text-xs px-2 py-0.5">
            {question.university}
          </Badge>
        </div>
        
        <Separator className="separator" />
        
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-3">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onUserClick(question.author_id, question.author_username);
              }}
              className="flex items-center gap-1.5 hover:text-orange-600 transition-colors cursor-pointer"
            >
              <Avatar className="h-5 w-5">
                <AvatarFallback className="bg-orange-100 text-orange-600 text-xs">
                  {question.author_username.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="underline text-xs">{question.author_username}</span>
            </button>
            <span className="text-gray-300">•</span>
            <span className="text-xs">{new Date(question.created_at).toLocaleString('tr-TR', { 
              timeZone: 'Europe/Istanbul',
              year: 'numeric',
              month: '2-digit', 
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            })}</span>
          </div>
          
          <div className="flex items-center gap-3">
            {user?.is_admin && (
              <div className="flex items-center gap-1">
                <Eye className="h-3 w-3" />
                <span className="text-xs">{question.view_count}</span>
              </div>
            )}
            
            <div className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              <span className="text-xs">{question.answer_count || 0}</span>
            </div>
            
            {canDelete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDelete}
                title="Soru sil"
                className="text-red-500 hover:text-red-700 p-2 rounded hover:bg-red-50 block sm:block"
                style={{ 
                  touchAction: 'manipulation',
                  WebkitTapHighlightColor: 'rgba(255, 0, 0, 0.1)',
                  userSelect: 'none'
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
            
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Answer Card Component with Reply Functionality
const AnswerCard = ({ answer, onUserClick, onReply, user, level = 0 }) => {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [replies, setReplies] = useState([]);
  const [showReplies, setShowReplies] = useState(false);
  const [replyLoading, setReplyLoading] = useState(false);
  const { toast } = useToast();
  const { user: authUser } = useAuth(); // AuthContext'ten user al
  const currentUser = user || authUser; // Prop'dan veya context'ten user kullan

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Europe/Istanbul'
    });
  };

  const handleDelete = async (e) => {
    e.stopPropagation();
    if (window.confirm('Bu cevabı silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`${API}/answers/${answer.id}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        window.location.reload(); // Refresh page
      } catch (err) {
        console.error('Cevap silme hatası:', err);
        alert('Hata: ' + (err.response?.data?.detail || 'Cevap silinemedi'));
      }
    }
  };

  const fetchReplies = async () => {
    try {
      const response = await axios.get(`${API}/answers/${answer.id}/replies`);
      setReplies(response.data.replies || []); // Fix: get replies from response.data.replies
      setShowReplies(true);
    } catch (err) {
      console.error('Replies yükleme hatası:', err);
      setReplies([]); // Set empty array on error
    }
  };

  const handleReplySubmit = async (e) => {
    e.preventDefault();
    
    // Yanıt validasyonu - minimum 4 karakter
    if (!replyContent.trim() || replyContent.trim().length < 4) {
      alert('Yanıt en az 4 karakter olmalıdır.');
      return;
    }

    setReplyLoading(true);
    try {
      const response = await axios.post(
        `${API}/answers/${answer.id}/replies`,
        { content: replyContent },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      
      setReplies([...replies, response.data]);
      setReplyContent('');
      setShowReplyForm(false);
      setShowReplies(true);
      
      // Başarı toastı göster
      toast({
        title: "✅ Başarılı!",
        description: "Yanıtınız başarıyla paylaşıldı.",
        variant: "success"
      });
      
      if (onReply) onReply();
    } catch (err) {
      console.error('Reply gönderme hatası:', err);
      
      // Handle rate limiting error
      if (err.response && err.response.status === 429) {
        alert(err.response.data.detail || 'Çok sık yanıt veriyorsunuz. Lütfen 2 dakika bekleyip tekrar deneyin.');
      } else {
        alert('Yanıt gönderilirken bir hata oluştu. Lütfen tekrar deneyin.');
      }
    } finally {
      setReplyLoading(false);
    }
  };

  const canDelete = currentUser && (currentUser.id === answer.author_id || currentUser.is_admin);

  return (
    <div className={`${level > 0 ? 'ml-8 border-l-2 border-orange-200 pl-4' : ''}`}>
      <Card className="shadow-lg mb-4">
        <CardContent className="p-6">
          <div className="flex justify-between items-start mb-4">
            <div className="flex-1">
              <div className="prose max-w-none">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {answer.content.split(/(@\w+)/g).map((part, index) => 
                    part.startsWith('@') ? (
                      <span key={index} className="bg-orange-100 text-orange-700 px-1 rounded font-medium">
                        {part}
                      </span>
                    ) : part
                  )}
                </p>
              </div>
            </div>
            
            {canDelete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDelete}
                title="Cevabı sil"
                className="text-red-500 hover:text-red-700 hover:bg-red-50 ml-2 min-w-[32px] min-h-[32px] touch-manipulation block sm:block"
                style={{ touchAction: 'manipulation' }}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
          
          <Separator className="my-4" />
          
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center gap-4">
              <button
                onClick={() => onUserClick(answer.author_id, answer.author_username)}
                className="flex items-center gap-2 hover:text-orange-600 transition-colors cursor-pointer"
              >
                <Avatar className="h-6 w-6">
                  <AvatarFallback className="bg-orange-100 text-orange-600 text-xs">
                    {answer.author_username.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <span className="underline">{answer.author_username}</span>
              </button>
              <span>•</span>
              <span>{formatDate(answer.created_at)}</span>
            </div>
            
            <div className="flex items-center gap-2">
              {answer.reply_count > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    if (showReplies) {
                      setShowReplies(false);
                    } else {
                      fetchReplies();
                      setShowReplies(true);
                    }
                  }}
                  className="text-orange-600 hover:text-orange-700"
                >
                  <MessageSquare className="h-4 w-4 mr-1" />
                  {showReplies ? 'Yanıtları gizle' : `${answer.reply_count} yanıt`}
                </Button>
              )}
              
              {user && level < 2 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowReplyForm(!showReplyForm)}
                  className="text-blue-600 hover:text-blue-700"
                >
                  <MessageSquare className="h-4 w-4 mr-1" />
                  Yanıtla
                </Button>
              )}
            </div>
          </div>

          {/* Reply Form */}
          {showReplyForm && user && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <form onSubmit={handleReplySubmit}>
                <Textarea
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  placeholder="Yanıtınızı yazın..."
                  className="mb-3 min-h-[80px] border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                />
                <div className="flex gap-2">
                  <Button 
                    type="submit"
                    size="sm"
                    disabled={replyLoading || !replyContent.trim()}
                    className="bg-orange-500 hover:bg-orange-600 text-white"
                  >
                    {replyLoading ? 'Gönderiliyor...' : 'Yanıt Gönder'}
                  </Button>
                  <Button 
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowReplyForm(false)}
                    className="border-gray-300 text-gray-600 hover:bg-gray-50"
                  >
                    İptal
                  </Button>
                </div>
              </form>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Replies */}
      {showReplies && replies.length > 0 && (
        <div className="space-y-2">
          {replies.map((reply) => (
            <AnswerCard
              key={reply.id}
              answer={reply}
              onUserClick={onUserClick}
              onReply={onReply}
              user={user}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Answer Form Component with File Upload
const AnswerForm = ({ questionId, onAnswerCreated, user }) => {
  const [newAnswer, setNewAnswer] = useState('');
  const [answerLoading, setAnswerLoading] = useState(false);
  const [answerError, setAnswerError] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploadLoading, setUploadLoading] = useState(false);
  const { toast } = useToast();

  const handleFileUpload = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    setUploadLoading(true);
    
    try {
      for (let file of files) {
        // Check file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
          alert(`${file.name} dosyası 10MB'den büyük. Lütfen daha küçük bir dosya seçin.`);
          continue;
        }
        
        // Check file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
        if (!allowedTypes.includes(file.type)) {
          alert(`${file.name} desteklenmeyen dosya formatı. Sadece PNG, JPG, GIF, WebP ve PDF dosyaları yüklenebilir.`);
          continue;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(`${API}/files/upload`, formData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        
        setUploadedFiles(prev => [...prev, {
          id: response.data.file_id,
          name: file.name,
          size: file.size,
          type: file.type
        }]);
      }
    } catch (err) {
      console.error('Dosya yükleme hatası:', err);
      alert('Dosya yükleme sırasında bir hata oluştu');
    } finally {
      setUploadLoading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Cevap validasyonu - minimum 4 karakter
    if (!newAnswer.trim() || newAnswer.trim().length < 4) {
      setAnswerError('Cevap en az 4 karakter olmalıdır.');
      return;
    }

    setAnswerLoading(true);
    try {
      const answerData = {
        content: newAnswer,
        attachments: uploadedFiles.map(file => file.id)
      };
      
      const response = await axios.post(`${API}/questions/${questionId}/answers`, answerData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      onAnswerCreated(response.data);
      setNewAnswer('');
      setUploadedFiles([]);
      setAnswerError(''); // Clear error on successful submission
      
      // Başarı toastı göster
      toast({
        title: "✅ Başarılı!",
        description: "Cevabınız başarıyla paylaşıldı.",
        variant: "success"
      });
    } catch (err) {
      console.error('Cevap gönderme hatası:', err);
      
      // Handle profanity error
      if (err.response && err.response.status === 400 && err.response.data.detail && err.response.data.detail.includes('uygunsuz kelime')) {
        setAnswerError(err.response.data.detail);
        toast.error(err.response.data.detail, {
          duration: 5000
        });
      }
      // Handle rate limiting error
      else if (err.response && err.response.status === 429) {
        setAnswerError(err.response.data.detail || 'Çok sık cevap veriyorsunuz. Lütfen bekleyip tekrar deneyin.');
      } else {
        setAnswerError('Cevap gönderilirken bir hata oluştu. Lütfen tekrar deneyin.');
      }
    } finally {
      setAnswerLoading(false);
    }
  };

  if (!user) {
    return (
      <Card className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <Users className="h-5 w-5 text-blue-500" />
            <div>
              <p className="text-sm font-medium text-blue-900">
                Bu soruya cevap vermek ve etiketlemek için giriş yapın
              </p>
              <p className="text-xs text-blue-700">
                Şimdilik sadece mevcut soruları görüntüleyebilirsiniz
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mb-6 shadow-lg border-orange-200">
      <CardHeader>
        <CardTitle className="text-lg text-gray-900">Cevabınızı Yazın</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="answer">Cevap</Label>
            <Textarea
              id="answer"
              value={newAnswer}
              onChange={(e) => {
                setNewAnswer(e.target.value);
                if (answerError) setAnswerError(''); // Clear error when user starts typing
              }}
              placeholder="Cevabınızı yazın... (@kullaniciadi ile kullanıcıları etiketleyebilirsiniz)"
              className="border-gray-300 focus:border-orange-500 focus:ring-orange-500 min-h-[120px]"
              required
            />
          </div>

          {/* File Upload Section */}
          <div className="space-y-2">
            <Label>Dosya Ekle (İsteğe Bağlı)</Label>
            <div className="border-2 border-dashed border-orange-300 rounded-lg p-4 hover:border-orange-400 transition-colors">
              <input
                type="file"
                multiple
                accept=".png,.jpg,.jpeg,.gif,.webp,.pdf"
                onChange={handleFileUpload}
                className="hidden"
                id="answer-file-upload"
                disabled={uploadLoading}
              />
              <label 
                htmlFor="answer-file-upload" 
                className="cursor-pointer flex flex-col items-center gap-2 text-center"
              >
                <Upload className="h-8 w-8 text-orange-500" />
                <div>
                  <p className="text-sm font-medium text-gray-700">
                    {uploadLoading ? 'Yükleniyor...' : 'Dosya seç veya buraya sürükle'}
                  </p>
                  <p className="text-xs text-gray-500">
                    PNG, JPG, GIF, WebP, PDF (Maks 10MB)
                  </p>
                </div>
              </label>
            </div>
            
            {/* Uploaded Files */}
            {uploadedFiles.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700">Yüklenen Dosyalar:</p>
                {uploadedFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-2 bg-orange-50 rounded-md">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <span className="text-xs text-gray-500">({formatFileSize(file.size)})</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(file.id)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {answerError && (
            <div className="text-red-600 text-sm text-center bg-red-50 p-2 rounded">
              {answerError}
            </div>
          )}

          <Button 
            type="submit" 
            disabled={answerLoading || !newAnswer.trim() || uploadLoading}
            className="bg-orange-500 hover:bg-orange-600 text-white"
          >
            {answerLoading ? 'Gönderiliyor...' : 'Cevap Gönder'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

// Pagination Component
const Pagination = ({ pagination, currentPage, onPageChange }) => {
  if (!pagination || pagination.total_pages <= 1) return null;

  const { current_page, total_pages, has_prev, has_next } = pagination;
  
  const getPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;
    
    let startPage = Math.max(1, current_page - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(total_pages, startPage + maxVisiblePages - 1);
    
    // Adjust start page if we're near the end
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // Add first page and ellipsis if needed
    if (startPage > 1) {
      pages.push(1);
      if (startPage > 2) {
        pages.push('...');
      }
    }
    
    // Add visible pages
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    // Add ellipsis and last page if needed
    if (endPage < total_pages) {
      if (endPage < total_pages - 1) {
        pages.push('...');
      }
      pages.push(total_pages);
    }
    
    return pages;
  };

  return (
    <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-8">
      {/* Mobile: Page Info Top */}
      <span className="text-sm text-gray-500 order-first sm:order-last">
        Sayfa {current_page} / {total_pages} ({pagination?.total_count || 0} soru)
      </span>
      
      {/* Pagination Controls */}
      <div className="flex items-center gap-2">
        {/* Previous Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(current_page - 1)}
          disabled={!has_prev}
          className="border-orange-300 text-orange-600 hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm px-2 sm:px-3"
        >
          <span className="hidden sm:inline">‹ Önceki</span>
          <span className="sm:hidden">‹</span>
        </Button>

        {/* Page Numbers */}
        <div className="flex gap-1">
          {getPageNumbers().map((page, index) => (
            <div key={index}>
              {page === '...' ? (
                <span className="px-2 py-2 text-gray-500 text-sm">...</span>
              ) : (
                <Button
                  variant={page === current_page ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onPageChange(page)}
                  className={`text-xs sm:text-sm px-2 sm:px-3 py-2 min-w-[32px] ${page === current_page
                    ? 'bg-orange-500 hover:bg-orange-600 text-white'
                    : 'border-orange-300 text-orange-600 hover:bg-orange-50'
                  }`}
                >
                  {page}
                </Button>
              )}
            </div>
          ))}
        </div>

        {/* Next Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(current_page + 1)}
          disabled={!has_next}
          className="border-orange-300 text-orange-600 hover:bg-orange-50 disabled:opacity-50 disabled:cursor-not-allowed text-xs sm:text-sm px-2 sm:px-3"
        >
          <span className="hidden sm:inline">Sonraki ›</span>
          <span className="sm:hidden">›</span>
        </Button>
      </div>
    </div>
  );
};

// Notifications Modal Component
const NotificationsModal = ({ isOpen, onClose, user, onNotificationClick }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (isOpen && user) {
      fetchNotifications();
      fetchUnreadCount();
    }
  }, [isOpen, user]);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/notifications`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setNotifications(response.data.notifications || []); // Fix: get notifications array from response
    } catch (err) {
      console.error('Bildirimler yüklenirken hata:', err);
      setNotifications([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await axios.get(`${API}/notifications/unread-count`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setUnreadCount(response.data.unread_count);
    } catch (err) {
      console.error('Okunmamış bildirim sayısı alınırken hata:', err);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.put(`${API}/notifications/${notificationId}/read`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      // Update local state
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, is_read: true } : n
      ));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (err) {
      console.error('Bildirim okundu olarak işaretlenirken hata:', err);
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'answer': return <MessageSquare className="h-4 w-4 text-green-500" />;
      case 'reply': return <Activity className="h-4 w-4 text-blue-500" />;
      case 'mention': return <Users className="h-4 w-4 text-orange-500" />;
      default: return <Bell className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatTimeAgo = (dateString) => {
    // Türkiye saatine göre hesaplama
    const date = new Date(dateString);
    const now = new Date();
    
    // Istanbul timezone'una göre ayarla
    const istanbulDate = new Date(date.toLocaleString("en-US", {timeZone: "Europe/Istanbul"}));
    const istanbulNow = new Date(now.toLocaleString("en-US", {timeZone: "Europe/Istanbul"}));
    
    const diffMs = istanbulNow - istanbulDate;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Az önce';
    if (diffMins < 60) return `${diffMins} dakika önce`;
    if (diffHours < 24) return `${diffHours} saat önce`;
    if (diffDays < 7) return `${diffDays} gün önce`;
    return date.toLocaleDateString('tr-TR', { timeZone: 'Europe/Istanbul' });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-lg flex items-center gap-2">
            <Bell className="h-5 w-5 text-orange-500" />
            Bildirimler
            {unreadCount > 0 && (
              <Badge className="bg-red-500 text-white text-xs">
                {unreadCount}
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>
        
        <div className="mt-4">
          {loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse bg-gray-200 h-16 rounded"></div>
              ))}
            </div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-6 text-gray-500">
              <Bell className="h-8 w-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">Henüz bildirim yok</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 hover:shadow-md ${
                    notification.is_read ? 'bg-white' : 'bg-blue-50 border-blue-200'
                  }`}
                  onClick={() => onNotificationClick(notification)}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-1">
                      {getNotificationIcon(notification.type)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm text-gray-900">
                        {notification.title}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-400 mt-2">
                        {formatTimeAgo(notification.created_at)}
                      </p>
                    </div>
                    
                    {!notification.is_read && (
                      <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-2"></div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Profile Modal Component
const ProfileModal = ({ isOpen, onClose, user, onQuestionClick }) => {
  const [activeTab, setActiveTab] = useState('questions');
  const [myQuestions, setMyQuestions] = useState([]);
  const [myAnswers, setMyAnswers] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && user) {
      fetchProfileData();
    }
  }, [isOpen, user, activeTab]);

  const fetchProfileData = async () => {
    setLoading(true);
    try {
      // Fetch stats
      const statsResponse = await axios.get(`${API}/profile/stats`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setStats(statsResponse.data);

      // Fetch questions or answers based on active tab
      if (activeTab === 'questions') {
        const questionsResponse = await axios.get(`${API}/profile/my-questions`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setMyQuestions(questionsResponse.data);
      } else {
        const answersResponse = await axios.get(`${API}/profile/my-answers`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setMyAnswers(answersResponse.data);
      }
    } catch (err) {
      console.error('Profil verileri yüklenirken hata:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm('Bu soruyu silmek istediğinizden emin misiniz?')) return;
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        alert('Lütfen giriş yapın');
        return;
      }
      
      await axios.delete(`${API}/questions/${questionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      alert('Soru silindi!');
      setMyQuestions(myQuestions.filter(q => q.id !== questionId));
      
    } catch (err) {
      alert('Hata: ' + (err.response?.data?.detail || 'Silme başarısız'));
    }
  };

  const handleDeleteAnswer = async (answerId) => {
    if (window.confirm('Bu cevabı silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`${API}/answers/${answerId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setMyAnswers(myAnswers.filter(a => a.id !== answerId));
      } catch (err) {
        console.error('Cevap silme hatası:', err);
        alert('Hata: ' + (err.response?.data?.detail || 'Cevap silinemedi'));
      }
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-lg flex items-center gap-2">
            <Settings className="h-5 w-5 text-orange-500" />
            Profilim
          </DialogTitle>
        </DialogHeader>
        
        <div className="mt-4">
          {/* Profile Header */}
          <div className="bg-gradient-to-r from-orange-50 to-orange-100 p-4 rounded-lg mb-6">
            <div className="flex items-center gap-4">
              <Avatar className="h-16 w-16">
                <AvatarFallback className="bg-orange-500 text-white text-2xl">
                  {user?.username?.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="text-xl font-bold text-gray-900">{user?.username}</h3>
                <p className="text-gray-600">{user?.email}</p>
                <p className="text-sm text-gray-500">{user?.university} - {user?.faculty}</p>
                <p className="text-sm text-gray-500">{user?.department}</p>
              </div>
              {user?.is_admin && (
                <Badge className="bg-red-100 text-red-800">Admin</Badge>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats.questions_count || 0}</div>
              <div className="text-sm text-blue-800">Sorular</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats.answers_count || 0}</div>
              <div className="text-sm text-green-800">Cevaplar</div>
            </div>

          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-4">
            <Button
              variant={activeTab === 'questions' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('questions')}
              className={activeTab === 'questions' 
                ? 'bg-orange-500 hover:bg-orange-600' 
                : 'border-orange-300 text-orange-600 hover:bg-orange-50'
              }
            >
              Sorularım ({stats.questions_count || 0})
            </Button>
            <Button
              variant={activeTab === 'answers' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('answers')}
              className={activeTab === 'answers' 
                ? 'bg-orange-500 hover:bg-orange-600' 
                : 'border-orange-300 text-orange-600 hover:bg-orange-50'
              }
            >
              Cevaplarım ({stats.answers_count || 0})
            </Button>
          </div>

          {/* Content */}
          <div className="min-h-[300px]">
            {loading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="animate-pulse bg-gray-200 h-20 rounded"></div>
                ))}
              </div>
            ) : activeTab === 'questions' ? (
              <div className="space-y-3">
                {myQuestions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <MessageSquare className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                    <p>Henüz soru sormadınız</p>
                  </div>
                ) : (
                  myQuestions.map((question) => (
                    <div 
                      key={question.id} 
                      className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => {
                        onClose(); // Close profile modal
                        if (onQuestionClick) {
                          onQuestionClick(question.id);
                        }
                      }}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 mb-2">{question.title}</h4>
                          <p className="text-sm text-gray-600 mb-2 line-clamp-2">{question.content}</p>
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <Badge className="bg-orange-100 text-orange-800">{question.category}</Badge>
                            <span>•</span>
                            <span>{new Date(question.created_at).toLocaleString('tr-TR', { 
                              timeZone: 'Europe/Istanbul',
                              year: 'numeric',
                              month: '2-digit', 
                              day: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}</span>
                            <span>•</span>
                            <span>{question.answer_count || 0} cevap</span>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteQuestion(question.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {myAnswers.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Activity className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                    <p>Henüz cevap vermediniz</p>
                  </div>
                ) : (
                  myAnswers.map((answer) => (
                    <div 
                      key={answer.id} 
                      className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => {
                        onClose(); // Close profile modal  
                        if (onQuestionClick && answer.question_id) {
                          onQuestionClick(answer.question_id);
                        }
                      }}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <p className="text-sm text-gray-700 mb-2 line-clamp-3">{answer.content}</p>
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <span>{new Date(answer.created_at).toLocaleString('tr-TR', { 
                              timeZone: 'Europe/Istanbul',
                              year: 'numeric',
                              month: '2-digit', 
                              day: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}</span>
                            {answer.parent_answer_id ? (
                              <>
                                <span>•</span>
                                <Badge variant="outline" className="text-xs">Yanıt</Badge>
                              </>
                            ) : (
                              <>
                                <span>•</span>
                                <Badge variant="outline" className="text-xs">Cevap</Badge>
                              </>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteAnswer(answer.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Admin Panel Modal Component
const AdminPanelModal = ({ isOpen, onClose, user }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (isOpen && user?.is_admin) {
      fetchUsers();
    }
  }, [isOpen, user]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setUsers(response.data.users);
    } catch (err) {
      console.error('Kullanıcılar yüklenirken hata:', err);
    } finally {
      setLoading(false);
    }
  };

  const searchUsers = async (term) => {
    if (!term || term.trim().length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      const response = await axios.get(`${API}/admin/search-users?q=${encodeURIComponent(term)}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setSearchResults(response.data.users);
    } catch (err) {
      console.error('Kullanıcı arama hatası:', err);
      alert('Hata: ' + (err.response?.data?.detail || 'Arama başarısız'));
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchChange = (e) => {
    const term = e.target.value;
    setSearchTerm(term);
    
    // Debounce search - 500ms after user stops typing
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
      searchUsers(term);
    }, 500);
  };

  const clearSearch = () => {
    setSearchTerm('');
    setSearchResults([]);
    setIsSearching(false);
  };

  // UserRow component for reusability
  const UserRow = ({ userData, currentUser }) => (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3">
        <Avatar className="h-10 w-10">
          <AvatarFallback className={userData.is_admin ? "bg-red-100 text-red-600" : "bg-blue-100 text-blue-600"}>
            {userData.username.charAt(0).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        
        <div>
          <p className="font-medium text-gray-900">
            {userData.username} 
            {userData.is_admin && <Badge className="ml-2 bg-red-100 text-red-800">Admin</Badge>}
            {userData.is_suspended && <Badge className="ml-2 bg-yellow-100 text-yellow-800">Askıda</Badge>}
            {userData.is_muted && <Badge className="ml-2 bg-gray-100 text-gray-800">Susturulmuş</Badge>}
          </p>
          <p className="text-sm text-gray-500">{userData.email}</p>
          <p className="text-xs text-gray-400">{userData.university} - {userData.faculty}</p>
          <p className="text-xs text-gray-400">{userData.question_count} soru, {userData.answer_count} cevap</p>
          {userData.is_suspended && userData.suspend_until && (
            <p className="text-xs text-red-500">Askı bitiş: {new Date(userData.suspend_until).toLocaleString('tr-TR', { 
              timeZone: 'Europe/Istanbul',
              year: 'numeric',
              month: '2-digit', 
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            })}</p>
          )}
          {userData.suspend_reason && (
            <p className="text-xs text-red-500">Sebep: {userData.suspend_reason}</p>
          )}
          {userData.is_muted && userData.mute_until && (
            <p className="text-xs text-orange-500">Susturma bitiş: {new Date(userData.mute_until).toLocaleString('tr-TR', { 
              timeZone: 'Europe/Istanbul',
              year: 'numeric',
              month: '2-digit', 
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            })}</p>
          )}
        </div>
      </div>
      
      <div className="flex flex-col gap-1">
        {/* Admin Controls */}
        <div className="flex gap-1">
          {userData.is_admin ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleRemoveAdmin(userData.id)}
              className="border-red-300 text-red-600 hover:bg-red-50 text-xs px-2 py-1"
              disabled={userData.id === currentUser.id}
            >
              Admin Kaldır
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleMakeAdmin(userData.id)}
              className="border-green-300 text-green-600 hover:bg-green-50 text-xs px-2 py-1"
            >
              Admin Yap
            </Button>
          )}
        </div>
        
        {/* Suspend Controls */}
        <div className="flex gap-1">
          {userData.is_suspended ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleUnsuspendUser(userData.id, userData.username)}
              className="border-blue-300 text-blue-600 hover:bg-blue-50 text-xs px-2 py-1"
            >
              Askıyı Kaldır
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSuspendUser(userData.id, userData.username)}
              className="border-yellow-300 text-yellow-600 hover:bg-yellow-50 text-xs px-2 py-1"
              disabled={userData.id === currentUser.id || userData.is_admin}
            >
              Askıya Al
            </Button>
          )}
        </div>
        
        {/* Delete User */}
        <div className="flex gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDeleteUser(userData.id, userData.username)}
            className="border-red-500 text-red-700 hover:bg-red-100 text-xs px-2 py-1"
            disabled={userData.id === currentUser.id}
          >
            🗑️ Kullanıcı Sil
          </Button>
        </div>
      </div>
    </div>
  );

  const handleMakeAdmin = async (userId) => {
    try {
      await axios.post(`${API}/admin/make-admin/${userId}`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      fetchUsers(); // Refresh list
    } catch (err) {
      console.error('Admin yapma hatası:', err);
      alert('Hata: ' + (err.response?.data?.detail || 'Admin yapılamadı'));
    }
  };

  const handleRemoveAdmin = async (userId) => {
    if (window.confirm('Admin haklarını kaldırmak istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`${API}/admin/remove-admin/${userId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        fetchUsers(); // Refresh list
      } catch (err) {
        console.error('Admin hakları kaldırma hatası:', err);
        alert('Hata: ' + (err.response?.data?.detail || 'Admin hakları kaldırılamadı'));
      }
    }
  };

  const handleSuspendUser = async (userId, username) => {
    const days = prompt(`${username} kullanıcısını kaç gün askıya almak istiyorsunuz? (1-365)`, '3');
    if (!days || isNaN(days) || days < 1 || days > 365) {
      alert('Lütfen 1-365 arasında geçerli bir sayı girin');
      return;
    }
    
    const reason = prompt('Askıya alma sebebini yazın:', '');
    if (!reason) return;
    
    try {
      await axios.post(`${API}/admin/suspend-user/${userId}`, {
        suspend_days: parseInt(days),
        reason: reason
      }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      alert(`${username} kullanıcısı ${days} gün askıya alındı`);
      fetchUsers(); // Refresh list
    } catch (err) {
      console.error('Askıya alma hatası:', err);
      alert('Hata: ' + (err.response?.data?.detail || 'Askıya alma başarısız'));
    }
  };

  const handleUnsuspendUser = async (userId, username) => {
    if (window.confirm(`${username} kullanıcısının askısını kaldırmak istediğinizden emin misiniz?`)) {
      try {
        await axios.post(`${API}/admin/unsuspend-user/${userId}`, {}, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        alert(`${username} kullanıcısının askısı kaldırıldı`);
        fetchUsers(); // Refresh list
      } catch (err) {
        console.error('Askı kaldırma hatası:', err);
        alert('Hata: ' + (err.response?.data?.detail || 'Askı kaldırma başarısız'));
      }
    }
  };

  const handleDeleteUser = async (userId, username) => {
    if (window.confirm(`${username} kullanıcısını kalıcı olarak silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!`)) {
      if (window.confirm('Son kez soralım: Kullanıcı hesabını kalıcı olarak sileceksiniz. Emin misiniz?')) {
        try {
          await axios.delete(`${API}/admin/delete-user/${userId}`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          });
          alert(`${username} kullanıcısı silindi`);
          fetchUsers(); // Refresh list
        } catch (err) {
          console.error('Kullanıcı silme hatası:', err);
          alert('Hata: ' + (err.response?.data?.detail || 'Kullanıcı silinemedi'));
        }
      }
    }
  };

  const createSuperAdmin = async () => {
    try {
      const response = await axios.post(`${API}/create-super-admin`);
      alert('Super admin oluşturuldu!\nKullanıcı adı: admin\nŞifre: admin123');
    } catch (err) {
      alert('Hata: ' + (err.response?.data?.detail || 'Super admin oluşturulamadı'));
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-lg flex items-center gap-2">
            <Users className="h-5 w-5 text-red-500" />
            Admin Paneli
          </DialogTitle>
        </DialogHeader>
        
        {!user?.is_admin ? (
          <div className="text-center py-6">
            <p className="text-red-600 mb-4">Bu sayfaya erişim yetkiniz yok.</p>
            <Button
              onClick={createSuperAdmin}
              className="bg-red-500 hover:bg-red-600 text-white"
            >
              İlk Super Admin Oluştur
            </Button>
          </div>
        ) : (
          <div className="mt-4">
            <h3 className="font-semibold mb-4">Kullanıcı Yönetimi</h3>
            
            {/* Search Section */}
            <div className="mb-6 space-y-3">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Kullanıcı ara (isim, email, üniversite)..."
                  value={searchTerm}
                  onChange={handleSearchChange}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
                {searchTerm && (
                  <Button
                    variant="outline"
                    onClick={clearSearch}
                    className="px-3"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              
              {isSearching && (
                <div className="text-sm text-gray-500 flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-500"></div>
                  Kullanıcılar aranıyor...
                </div>
              )}
              
              {searchTerm && searchResults.length === 0 && !isSearching && (
                <div className="text-sm text-gray-500">
                  "{searchTerm}" için kullanıcı bulunamadı
                </div>
              )}
            </div>
            
            {loading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="animate-pulse bg-gray-200 h-16 rounded"></div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {/* Admin Users Section */}
                {!searchTerm && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      👑 Admin Kullanıcıları ({users.length})
                    </h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {users.map((userData) => (
                        <UserRow key={userData.id} userData={userData} currentUser={user} />
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Search Results Section */}
                {searchTerm && searchResults.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      🔍 Arama Sonuçları "{searchTerm}" ({searchResults.length})
                    </h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto">
                      {searchResults.map((userData) => (
                        <UserRow key={userData.id} userData={userData} currentUser={user} />
                      ))}
                    </div>
                  </div>
                )}
                
                {/* No results message */}
                {!searchTerm && users.length === 0 && (
                  <div className="text-center py-6 text-gray-500">
                    Henüz admin kullanıcı bulunamadı
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

// Leaderboard Modal Component  
const LeaderboardModal = ({ isOpen, onClose, leaderboard, loading, fetchLeaderboard }) => {

  useEffect(() => {
    if (isOpen && fetchLeaderboard) {
      fetchLeaderboard();
    }
  }, [isOpen, fetchLeaderboard]);

  const getRankIcon = (index) => {
    switch (index) {
      case 0: return <Crown className="h-5 w-5 text-yellow-500" />;
      case 1: return <Award className="h-5 w-5 text-gray-400" />;
      case 2: return <Trophy className="h-5 w-5 text-orange-600" />;
      default: return <Star className="h-4 w-4 text-orange-400" />;
    }
  };

  const getRankColor = (index) => {
    switch (index) {
      case 0: return "bg-gradient-to-r from-yellow-50 to-yellow-100 border-yellow-200";
      case 1: return "bg-gradient-to-r from-gray-50 to-gray-100 border-gray-200";
      case 2: return "bg-gradient-to-r from-orange-50 to-orange-100 border-orange-200";
      default: return "bg-white border-gray-200";
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b p-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-orange-500" />
            <h2 className="text-lg font-bold">Haftalık Liderler</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-sm text-gray-600 mb-4">Son 7 gündeki en aktif üyeler</p>
          
          {loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse bg-gray-200 h-12 rounded"></div>
              ))}
            </div>
          ) : leaderboard.length === 0 ? (
            <div className="text-center py-6 text-gray-500">
              <Trophy className="h-8 w-8 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">Henüz veri yok</p>
              <p className="text-xs mt-1">Son 7 gün içinde aktif kullanıcı bulunmuyor</p>
            </div>
          ) : (
            <div className="space-y-2">
              {leaderboard.map((user, index) => (
                <div key={index} className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${getRankColor(index)}`}>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      {getRankIcon(index)}
                      <span className="font-semibold text-gray-900">#{user.rank}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{user.username}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>🏫 {user.university}</span>
                        <span>•</span>
                        <span>🎯 {user.total_points} puan</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {user.question_count}S + {user.answer_count}C
                    </div>
                    <div className="text-xs text-gray-500">
                      Soru + Cevap
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Main Forum Component
const Forum = ({ globalLeaderboard, leaderboardLoading, fetchGlobalLeaderboard }) => {
  const [questions, setQuestions] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [showAnswerForm, setShowAnswerForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredQuestions, setFilteredQuestions] = useState([]);

  // Category click handler
  const handleCategoryClick = (category) => {
    setSelectedCategory(category);
    setCurrentPage(1); // Reset to first page when filtering
  };
  const [showAllAnswers, setShowAllAnswers] = useState(false);
  const [rateLimitMessage, setRateLimitMessage] = useState('');
  const [answers, setAnswers] = useState([]);
  const [newAnswer, setNewAnswer] = useState('');
  const [loading, setLoading] = useState(true);
  const [answerLoading, setAnswerLoading] = useState(false);
  const [answerError, setAnswerError] = useState('');
  const [categories, setCategories] = useState({});
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showAllCategories, setShowAllCategories] = useState(false); // New state for categories expansion
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [selectedUsername, setSelectedUsername] = useState('');
  const [showLeaderboardModal, setShowLeaderboardModal] = useState(false);
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pagination, setPagination] = useState({});
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  
  // Get auth context FIRST
  const { token, user, logout, setUser } = useAuth();
  const navigate = useNavigate();

  // Session timeout - 50 minutes inactivity
  const SESSION_TIMEOUT = 50 * 60 * 1000; // 50 minutes in milliseconds

  // Update last activity timestamp
  const updateLastActivity = () => {
    localStorage.setItem('lastActivity', Date.now().toString());
  };

  // Check if session has expired
  const checkSessionTimeout = () => {
    const lastActivity = localStorage.getItem('lastActivity');
    if (!lastActivity || !user) return;

    const timeSinceLastActivity = Date.now() - parseInt(lastActivity);
    
    if (timeSinceLastActivity > SESSION_TIMEOUT) {
      // Session expired - logout user
      toast.warning("Oturum süresi doldu. Lütfen tekrar giriş yapın.", {
        duration: 5000
      });
      
      // Clear user data and redirect to home
      setUser(null);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('lastActivity');
      navigate('/');
    }
  };

  // Add activity listeners
  useEffect(() => {
    if (!user) return;

    // Initialize interval variable first
    let timeoutInterval;

    // Update activity on any user interaction
    const handleUserActivity = () => {
      updateLastActivity();
    };

    // Add event listeners for user interactions
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
    
    events.forEach(event => {
      document.addEventListener(event, handleUserActivity, true);
    });

    // Check session timeout on component mount and every 30 seconds
    checkSessionTimeout();
    timeoutInterval = setInterval(checkSessionTimeout, 30000);

    // Initial activity update
    updateLastActivity();

    return () => {
      // Cleanup event listeners
      events.forEach(event => {
        document.removeEventListener(event, handleUserActivity, true);
      });
      if (timeoutInterval) {
        clearInterval(timeoutInterval);
      }
    };
  }, [user, navigate, toast]);

  // Handle browser back button
  useEffect(() => {
    const handlePopState = (event) => {
      if (selectedQuestion) {
        setSelectedQuestion(null);
        window.history.replaceState(null, '', window.location.pathname);
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [selectedQuestion]);

  useEffect(() => {
    fetchQuestions();
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchQuestions();
    if (user) {
      fetchUnreadCount();
    }
  }, [selectedCategory, user, currentPage]);

  const fetchQuestions = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedCategory) {
        params.append('category', selectedCategory);
      }
      params.append('page', currentPage.toString());
      params.append('limit', '15');
      
      const response = await axios.get(`${API}/questions?${params.toString()}`);
      setQuestions(response.data || []);
      setPagination(response.data.pagination || {});
    } catch (err) {
      console.error('Sorular yüklenirken hata:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories`);
      setCategories(response.data);
    } catch (err) {
      console.error('Kategori yükleme hatası:', err);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await axios.get(`${API}/notifications/unread-count`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUnreadCount(response.data.unread_count);
    } catch (err) {
      console.error('Okunmamış bildirim sayısı alınırken hata:', err);
    }
  };

  const fetchAnswers = async (questionId) => {
    try {
      const response = await axios.get(`${API}/questions/${questionId}/answers`);
      setAnswers(response.data.answers || []); // Fix: answers is nested in response.data.answers
    } catch (err) {
      console.error('Cevaplar yüklenirken hata:', err);
      setAnswers([]); // Set empty array on error
    }
  };

  const handleQuestionClick = async (question) => {
    setSelectedQuestion(question);
    await fetchAnswers(question.id);
    
    // Push to history for better back button behavior
    window.history.pushState({ questionId: question.id }, '', `#soru-${question.id}`);
  };

  const handleNotificationClick = (notification) => {
    // Close notification modal first
    setShowNotifications(false);
    
    // Navigate to related question if exists
    if (notification.related_question_id) {
      // Find question and open it
      const question = questions.find(q => q.id === notification.related_question_id);
      if (question) {
        setSelectedQuestion(question);
        fetchAnswers(notification.related_question_id);
      }
    }
    
    // Mark notification as read
    markNotificationAsRead(notification.id);
  };

  const markNotificationAsRead = async (notificationId) => {
    try {
      await axios.put(`${API}/notifications/${notificationId}/read`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
    } catch (err) {
      console.error('Bildirim okundu işaretlenemedi:', err);
    }
  };

  const handleQuestionSearch = (searchValue) => {
    setSearchTerm(searchValue);
    
    if (!searchValue.trim()) {
      setFilteredQuestions(questions);
      return;
    }
    
    const filtered = questions.filter(question => 
      question.title.toLowerCase().includes(searchValue.toLowerCase()) ||
      question.content.toLowerCase().includes(searchValue.toLowerCase()) ||
      question.category.toLowerCase().includes(searchValue.toLowerCase())
    );
    
    setFilteredQuestions(filtered);
  };

  // Update filtered questions when questions change
  useEffect(() => {
    if (searchTerm.trim()) {
      handleQuestionSearch(searchTerm);
    } else {
      setFilteredQuestions(questions);
    }
  }, [questions]);

  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
    setCurrentPage(1); // Reset to first page when category changes
  };

  const handleQuestionCreated = (newQuestion) => {
    setQuestions([newQuestion, ...questions]);
  };

  const handleLikeQuestion = async (questionId) => {
    if (!user) return;
    
    try {
      await axios.post(`${API}/questions/${questionId}/like`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update the selected question's like count
      const updatedQuestion = { ...selectedQuestion };
      if (updatedQuestion.liked_by_user) {
        updatedQuestion.likes = Math.max(0, (updatedQuestion.likes || 0) - 1);
        updatedQuestion.liked_by_user = false;
      } else {
        updatedQuestion.likes = (updatedQuestion.likes || 0) + 1;
        updatedQuestion.liked_by_user = true;
      }
      setSelectedQuestion(updatedQuestion);
    } catch (err) {
      console.error('Beğenme hatası:', err);
    }
  };

  const handleUserClick = (userId, username) => {
    setSelectedUserId(userId);
    setSelectedUsername(username);
    setShowProfileModal(true);
  };

  const handleCloseProfileModal = () => {
    setShowProfileModal(false);
    setSelectedUserId(null);
    setSelectedUsername('');
  };

  const handleAnswerSubmit = async (e) => {
    e.preventDefault();
    if (!newAnswer.trim()) return;

    setAnswerLoading(true);
    try {
      const response = await axios.post(
        `${API}/questions/${selectedQuestion.id}/answers`,
        { content: newAnswer },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAnswers([...answers, response.data]);
      setNewAnswer('');
      setAnswerError(''); // Clear error on successful submission
      
      // Update question answer count
      setSelectedQuestion({
        ...selectedQuestion,
        answer_count: selectedQuestion.answer_count + 1
      });
    } catch (err) {
      console.error('Cevap gönderme hatası:', err);
      
      // Handle profanity error
      if (err.response && err.response.status === 400 && err.response.data.detail && err.response.data.detail.includes('uygunsuz kelime')) {
        setAnswerError(err.response.data.detail);
        toast.error(err.response.data.detail, {
          duration: 5000
        });
      }
      // Handle rate limiting error
      else if (err.response && err.response.status === 429) {
        setAnswerError(err.response.data.detail || 'Çok sık cevap veriyorsunuz. Lütfen bekleyip tekrar deneyin.');
      } else {
        setAnswerError('Cevap gönderilirken bir hata oluştu. Lütfen tekrar deneyin.');
      }
    } finally {
      setAnswerLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Europe/Istanbul'
    });
  };

  if (selectedQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-orange-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.location.href = '/'}>
                <img 
                  src="https://customer-assets.emergentagent.com/job_student-forum-1/artifacts/0f9o2m08_ChatGPT%20Image%205%20Eyl%202025%2021_49_28.png" 
                  alt="unisoruyor.com logo" 
                  className="w-10 h-10 sm:w-12 sm:h-12 object-contain"
                />
                <h1 className="text-lg sm:text-2xl font-bold site-title">Üniversiteliler Soruyor</h1>
              </div>
              
              {/* Desktop Menu */}
              <div className="hidden md:flex items-center gap-4">
                {user && <span className="text-sm text-gray-600">Hoş geldin, {user.username}</span>}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowLeaderboardModal(true)}
                  className="border-orange-300 text-orange-600 hover:bg-orange-50"
                >
                  <Trophy className="h-4 w-4 mr-1" />
                  Liderler
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => setSelectedQuestion(null)}
                  className="border-orange-300 text-orange-600 hover:bg-orange-50"
                >
                  Geri Dön
                </Button>
                <Button 
                  variant="outline"
                  onClick={logout}
                  className="border-gray-300 text-gray-600 hover:bg-gray-50"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>

              {/* Mobile Hamburger Menu */}
              <div className="md:hidden">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowMobileMenu(!showMobileMenu)}
                  className="p-2"
                >
                  <div className="w-6 h-6 flex flex-col justify-center items-center">
                    <div className={`w-5 h-0.5 bg-gray-600 transition-all ${showMobileMenu ? 'rotate-45 translate-y-1.5' : ''}`}></div>
                    <div className={`w-5 h-0.5 bg-gray-600 my-1 transition-all ${showMobileMenu ? 'opacity-0' : ''}`}></div>
                    <div className={`w-5 h-0.5 bg-gray-600 transition-all ${showMobileMenu ? '-rotate-45 -translate-y-1.5' : ''}`}></div>
                  </div>
                </Button>
              </div>
            </div>

            {/* Mobile Menu Dropdown */}
            {showMobileMenu && (
              <>
                {/* Backdrop */}
                <div 
                  className="fixed inset-0 bg-black bg-opacity-25 z-40 md:hidden"
                  onClick={() => setShowMobileMenu(false)}
                />
                <div className="md:hidden absolute top-16 left-0 right-0 bg-white border-t border-orange-200 shadow-lg z-50">
                  <div className="px-4 py-2 space-y-2">
                  {user && (
                    <div className="text-sm text-gray-600 py-2 border-b border-gray-200">
                      Hoş geldin, {user.username}
                    </div>
                  )}
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setShowLeaderboardModal(true);
                      setShowMobileMenu(false);
                    }}
                    className="w-full justify-start text-orange-600 hover:bg-orange-50"
                  >
                    <Trophy className="h-4 w-4 mr-2" />
                    Liderlik Tablosu
                  </Button>
                  <Button 
                    variant="ghost"
                    onClick={() => {
                      setSelectedQuestion(null);
                      setShowMobileMenu(false);
                    }}
                    className="w-full justify-start text-orange-600 hover:bg-orange-50"
                  >
                    Geri Dön
                  </Button>
                  <Button 
                    variant="ghost"
                    onClick={() => {
                      logout();
                      setShowMobileMenu(false);
                    }}
                    className="w-full justify-start text-gray-600 hover:bg-gray-50"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Çıkış Yap
                  </Button>
                </div>
              </div>
              </>
            )}
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Question Detail */}
          <Card className="mb-6 shadow-lg">
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h1 className="text-2xl font-bold text-gray-900">{selectedQuestion.title}</h1>
                <div className="flex gap-2">
                  <Badge className="bg-orange-100 text-orange-800">{selectedQuestion.department}</Badge>
                  <Badge variant="outline">{selectedQuestion.school}</Badge>
                </div>
              </div>
              
              <div className="prose max-w-none mb-4">
                <p className="text-gray-700 whitespace-pre-wrap">{selectedQuestion.content}</p>
              </div>
              
              <Separator className="my-4" />
              
              <div className="flex items-center justify-between text-sm text-gray-500">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => handleUserClick(selectedQuestion.author_id, selectedQuestion.author_username)}
                    className="flex items-center gap-2 hover:text-orange-600 transition-colors cursor-pointer"
                  >
                    <Avatar className="h-6 w-6">
                      <AvatarFallback className="bg-orange-100 text-orange-600 text-xs">
                        {selectedQuestion.author_username.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <span className="underline">{selectedQuestion.author_username}</span>
                  </button>
                  <span>•</span>
                  <span>{formatDate(selectedQuestion.created_at)}</span>
                </div>
                
                <div className="flex items-center gap-4">
                  {user?.is_admin && (
                    <div className="flex items-center gap-1">
                      <Eye className="h-4 w-4" />
                      <span>{selectedQuestion.view_count}</span>
                    </div>
                  )}
                  
                  <div className="flex items-center gap-1">
                    <MessageSquare className="h-4 w-4" />
                    <span>{answers.length}</span>
                  </div>
                  
                  {/* Delete Button for Question Detail */}
                  {user && (user.id === selectedQuestion.author_id || user.is_admin) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={async (e) => {
                        e.stopPropagation();
                        if (window.confirm('Bu soruyu silmek istediğinizden emin misiniz?')) {
                          try {
                            await axios.delete(`${API}/questions/${selectedQuestion.id}`, {
                              headers: {
                                'Authorization': `Bearer ${token}`
                              }
                            });
                            setSelectedQuestion(null); // Go back to main page
                            fetchQuestions(); // Refresh questions
                            alert('Soru başarıyla silindi');
                          } catch (err) {
                            console.error('Delete error:', err);
                            if (err.response?.status === 401 || err.response?.status === 403) {
                              alert('Oturum süresi dolmuş olabilir. Lütfen çıkış yapıp tekrar giriş yapın.');
                              logout(); // Clear localStorage
                            } else {
                              alert('Hata: ' + (err.response?.data?.detail || 'Silme işlemi başarısız'));
                            }
                          }
                        }
                      }}
                      title="Soru sil"
                      className="text-red-500 hover:text-red-700 p-2 rounded hover:bg-red-50 block sm:block"
                      style={{ 
                        touchAction: 'manipulation',
                        WebkitTapHighlightColor: 'rgba(255, 0, 0, 0.1)',
                        userSelect: 'none'
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Answer Form - Conditional with Button */}
          {user && !showAnswerForm && (
            <div className="mb-6">
              <Button
                onClick={() => setShowAnswerForm(true)}
                className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 text-lg"
              >
                <MessageSquare className="h-5 w-5 mr-2" />
                Cevap Yaz
              </Button>
            </div>
          )}

          {user && showAnswerForm && (
            <Card className="mb-6 shadow-lg">
              <CardContent className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Cevabınızı Yazın</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowAnswerForm(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <AnswerForm 
                  questionId={selectedQuestion.id}
                  onAnswerCreated={(newAnswer) => {
                    setAnswers([...answers, newAnswer]);
                    setShowAnswerForm(false); // Hide form after successful submission
                  }}
                  user={user}
                />
              </CardContent>
            </Card>
          )}

          {/* Answers */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Cevaplar ({answers.length})
            </h2>
            
            {!user ? (
              <Card className="shadow-lg bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-200">
                <CardContent className="p-8 text-center">
                  <div className="mb-4">
                    <MessageSquare className="h-16 w-16 mx-auto text-orange-400 mb-3" />
                    <h3 className="text-xl font-semibold text-orange-800 mb-2">
                      Cevapları Görmek İçin Giriş Yapın
                    </h3>
                    <p className="text-orange-700 mb-4">
                      Bu sorunun {answers.length} cevabı var. Cevapları görmek ve soruya cevap vermek için üye olun.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Button 
                      onClick={() => window.location.href = '/login'}
                      className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-2"
                    >
                      <User className="h-4 w-4 mr-2" />
                      Giriş Yap / Kayıt Ol
                    </Button>
                    <p className="text-sm text-orange-600">
                      🎓 Ücretsiz üyelik ile tüm cevapları görün ve toplulukla etkileşime geçin
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : answers.length === 0 ? (
              <Card className="shadow-lg">
                <CardContent className="p-6 text-center text-gray-500">
                  <MessageSquare className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>Henüz cevap yok. İlk cevabı sen ver!</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {answers
                  .filter(answer => !answer.parent_answer_id) // Only show main answers, not replies
                  .slice(0, showAllAnswers ? answers.length : 3) // Show first 3 answers unless showing all
                  .map((answer) => (
                    <AnswerCard
                      key={answer.id}
                      answer={answer}
                      onUserClick={handleUserClick}
                      onReply={() => fetchAnswers(selectedQuestion.id)} // Refresh answers when reply is added
                      user={user}
                      level={0}
                    />
                  ))}
                
                {/* Show more answers button */}
                {answers.filter(answer => !answer.parent_answer_id).length > 3 && !showAllAnswers && (
                  <div className="text-center py-4">
                    <Button
                      variant="outline"
                      onClick={() => setShowAllAnswers(true)}
                      className="border-orange-300 text-orange-600 hover:bg-orange-50"
                    >
                      <ChevronDown className="h-4 w-4 mr-2" />
                      Daha Fazla Cevap Görüntüle ({answers.filter(answer => !answer.parent_answer_id).length - 3} cevap daha)
                    </Button>
                  </div>
                )}
                
                {/* Show less answers button */}
                {showAllAnswers && answers.filter(answer => !answer.parent_answer_id).length > 3 && (
                  <div className="text-center py-4">
                    <Button
                      variant="outline"
                      onClick={() => setShowAllAnswers(false)}
                      className="border-orange-300 text-orange-600 hover:bg-orange-50"
                    >
                      <ChevronUp className="h-4 w-4 mr-2" />
                      Daha Az Cevap Göster
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        </main>

        {/* Profile Modal */}
        {showProfileModal && (
          <UserProfileModal
            userId={selectedUserId}
            username={selectedUsername}
            onClose={handleCloseProfileModal}
          />
        )}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-orange-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.location.href = '/'}>
              <img 
                src="https://customer-assets.emergentagent.com/job_student-forum-1/artifacts/0f9o2m08_ChatGPT%20Image%205%20Eyl%202025%2021_49_28.png" 
                alt="unisoruyor.com logo" 
                className="w-10 h-10 sm:w-12 sm:h-12 object-contain"
              />
              <h1 className="text-lg sm:text-2xl font-bold site-title">unisoruyor.com</h1>
            </div>
            
            {/* Desktop Menu */}
            <div className="hidden md:flex items-center gap-4">
              {user ? (
                <>
                  <span className="text-sm text-gray-600">Hoş geldin, {user.username}</span>
                  
                  {/* Notifications Button */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowNotifications(true)}
                    className="border-blue-300 text-blue-600 hover:bg-blue-50 relative"
                  >
                    <Bell className="h-4 w-4 mr-1" />
                    Bildirimler
                    {unreadCount > 0 && (
                      <Badge className="absolute -top-2 -right-2 bg-red-500 text-white text-xs min-w-[1.25rem] h-5">
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </Badge>
                    )}
                  </Button>
                  
                  {/* Profile Button */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowProfile(true)}
                    className="border-green-300 text-green-600 hover:bg-green-50"
                  >
                    <Settings className="h-4 w-4 mr-1" />
                    Profil
                  </Button>
                  
                  {user.is_admin && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowAdminPanel(true)}
                      className="border-red-300 text-red-600 hover:bg-red-50"
                    >
                      <Users className="h-4 w-4 mr-1" />
                      Admin
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowLeaderboardModal(true)}
                    className="border-orange-300 text-orange-600 hover:bg-orange-50"
                  >
                    <Trophy className="h-4 w-4 mr-1" />
                    Liderler
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={logout}
                    className="border-gray-300 text-gray-600 hover:bg-gray-50"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Çıkış
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowLeaderboardModal(true)}
                    className="border-orange-300 text-orange-600 hover:bg-orange-50"
                  >
                    <Trophy className="h-4 w-4 mr-1" />
                    Liderler
                  </Button>
                  <Button 
                    onClick={() => window.location.href = '/login'}
                    className="bg-orange-500 hover:bg-orange-600 text-white"
                  >
                    <User className="h-4 w-4 mr-2" />
                    Giriş Yap
                  </Button>
                </>
              )}
            </div>

            {/* Mobile Hamburger Menu */}
            <div className="md:hidden">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowMobileMenu(!showMobileMenu)}
                className="p-2"
              >
                <div className="w-6 h-6 flex flex-col justify-center items-center">
                  <div className={`w-5 h-0.5 bg-gray-600 transition-all ${showMobileMenu ? 'rotate-45 translate-y-1.5' : ''}`}></div>
                  <div className={`w-5 h-0.5 bg-gray-600 my-1 transition-all ${showMobileMenu ? 'opacity-0' : ''}`}></div>
                  <div className={`w-5 h-0.5 bg-gray-600 transition-all ${showMobileMenu ? '-rotate-45 -translate-y-1.5' : ''}`}></div>
                </div>
              </Button>
            </div>
          </div>

          {/* Mobile Menu Dropdown */}
          {showMobileMenu && (
            <>
              {/* Backdrop */}
              <div 
                className="fixed inset-0 bg-black bg-opacity-25 z-40 md:hidden"
                onClick={() => setShowMobileMenu(false)}
              />
              <div className="md:hidden absolute top-16 left-0 right-0 bg-white border-t border-orange-200 shadow-lg z-50">
                <div className="px-4 py-2 space-y-2">
                {user ? (
                  <>
                    <div className="text-sm text-gray-600 py-2 border-b border-gray-200">
                      Hoş geldin, {user.username}
                    </div>
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setShowNotifications(true);
                        setShowMobileMenu(false);
                      }}
                      className="w-full justify-start text-blue-600 hover:bg-blue-50 relative"
                    >
                      <Bell className="h-4 w-4 mr-2" />
                      Bildirimler
                      {unreadCount > 0 && (
                        <Badge className="absolute right-2 bg-red-500 text-white text-xs min-w-[1.25rem] h-5">
                          {unreadCount > 99 ? '99+' : unreadCount}
                        </Badge>
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setShowProfile(true);
                        setShowMobileMenu(false);
                      }}
                      className="w-full justify-start text-green-600 hover:bg-green-50"
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      Profil
                    </Button>
                    {user.is_admin && (
                      <Button
                        variant="ghost"
                        onClick={() => {
                          setShowAdminPanel(true);
                          setShowMobileMenu(false);
                        }}
                        className="w-full justify-start text-red-600 hover:bg-red-50"
                      >
                        <Users className="h-4 w-4 mr-2" />
                        Admin Paneli
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setShowLeaderboardModal(true);
                        setShowMobileMenu(false);
                      }}
                      className="w-full justify-start text-orange-600 hover:bg-orange-50"
                    >
                      <Trophy className="h-4 w-4 mr-2" />
                      Liderlik Tablosu
                    </Button>
                    <Button 
                      variant="ghost"
                      onClick={() => {
                        logout();
                        setShowMobileMenu(false);
                      }}
                      className="w-full justify-start text-gray-600 hover:bg-gray-50"
                    >
                      <LogOut className="h-4 w-4 mr-2" />
                      Çıkış Yap
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setShowLeaderboardModal(true);
                        setShowMobileMenu(false);
                      }}
                      className="w-full justify-start text-orange-600 hover:bg-orange-50"
                    >
                      <Trophy className="h-4 w-4 mr-2" />
                      Liderlik Tablosu
                    </Button>
                    <Button 
                      variant="ghost"
                      onClick={() => {
                        navigate('/login');
                        setShowMobileMenu(false);
                      }}
                      className="w-full justify-start text-orange-600 hover:bg-orange-50"
                    >
                      <User className="h-4 w-4 mr-2" />
                      Giriş Yap
                    </Button>
                  </>
                )}
              </div>
            </div>
            </>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="text-center mb-8 py-8">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-6xl font-black mb-4 gradient-header leading-tight">
              Üniversiteliler Soruyor
            </h2>
            <p className="text-2xl subtitle-modern mb-4 font-semibold">
              Soru Sor • Cevap Al • Öğren
            </p>
            <p className="text-lg text-gray-600 mb-6 leading-relaxed">
              Türkiye'nin en büyük üniversite öğrenci topluluğu
            </p>
            <div className="flex items-center justify-center gap-8 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-orange-500" />
                <span>Binlerce Öğrenci</span>
              </div>
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-orange-500" />
                <span>Anlık Yardım</span>
              </div>
              <div className="flex items-center gap-2">
                <Trophy className="h-4 w-4 text-orange-500" />
                <span>Başarı Odaklı</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content - Full Width Layout */}
        <div className="max-w-5xl mx-auto">
          {/* Category Filter */}
          <CategoryFilter 
            selectedCategory={selectedCategory}
            onCategoryChange={handleCategoryChange}
            categories={categories}
          />

          {/* Question Form - Only for logged in users */}
          {user && <QuestionForm onQuestionCreated={handleQuestionCreated} />}

          {/* Guest Message */}
          {!user && (
            <Card className="mb-6 bg-gradient-to-r from-orange-50 to-yellow-50 border-orange-200">
              <CardContent className="p-6">
                <div className="text-center">
                  <div className="mb-4">
                    <Users className="h-12 w-12 mx-auto text-orange-500 mb-3" />
                    <h3 className="text-lg font-semibold text-orange-800 mb-2">
                      🎓 Toplulukla Buluş, Bilgi Paylaş!
                    </h3>
                    <p className="text-orange-700 mb-4">
                      Sorularını sor, deneyimli öğrencilerden cevap al. Cevapları görmek için üye ol.
                    </p>
                  </div>
                  <Button 
                    onClick={() => window.location.href = '/login'}
                    className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-2"
                  >
                    <User className="h-4 w-4 mr-2" />
                    Ücretsiz Üye Ol
                  </Button>
                  <p className="text-sm text-orange-600 mt-2">
                    ⭐ Tüm özellikler ücretsiz • ⚡ Hemen başla
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Questions List */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-gray-900">
                {selectedCategory ? `${selectedCategory} - Sorular` : 'Tüm Sorular'} ({pagination?.total_count || 0})
              </h3>
            </div>

            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto"></div>
                <p className="text-gray-500 mt-2">Sorular yükleniyor...</p>
              </div>
            ) : questions.length === 0 ? (
              <Card className="shadow-lg">
                <CardContent className="p-8 text-center text-gray-500">
                  <MessageSquare className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-medium mb-2">Henüz soru yok</h3>
                  <p>İlk soruyu sen sor ve topluluğu başlat!</p>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="grid grid-cols-1 gap-4">
                  {questions.map((question) => (
                    <QuestionCard
                      key={question.id}
                      question={question}
                      onClick={handleQuestionClick}
                      user={user}
                      onUserClick={handleUserClick}
                      onCategoryClick={handleCategoryClick}
                    />
                  ))}
                </div>
                
                {/* Pagination */}
                <Pagination 
                  pagination={pagination}
                  currentPage={currentPage}
                  onPageChange={setCurrentPage}
                />
              </>
            )}
          </div>
        </div>

        {/* Modals */}
        <NotificationsModal 
          isOpen={showNotifications} 
          onClose={() => setShowNotifications(false)}
          user={user}
          onNotificationClick={handleNotificationClick}
        />
        
        <ProfileModal 
          isOpen={showProfile} 
          onClose={() => setShowProfile(false)}
          user={user}
          onQuestionClick={handleQuestionClick}
        />
        
        <AdminPanelModal 
          isOpen={showAdminPanel} 
          onClose={() => setShowAdminPanel(false)}
          user={user}
        />
        
        <LeaderboardModal 
          isOpen={showLeaderboardModal} 
          onClose={() => setShowLeaderboardModal(false)}
          leaderboard={globalLeaderboard || []}
          loading={leaderboardLoading}
          fetchLeaderboard={fetchGlobalLeaderboard}
        />

        {showProfileModal && (
          <UserProfileModal
            userId={selectedUserId}
            username={selectedUsername}
            onClose={handleCloseProfileModal}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-orange-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Site Info */}
            <div className="text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-2 mb-4">
                <img 
                  src="https://customer-assets.emergentagent.com/job_student-forum-1/artifacts/0f9o2m08_ChatGPT%20Image%205%20Eyl%202025%2021_49_28.png" 
                  alt="unisoruyor.com logo" 
                  className="w-8 h-8 object-contain"
                />
                <h3 className="text-lg font-bold text-orange-600">unisoruyor.com</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Türkiye'nin en büyük üniversite öğrenci topluluğu
              </p>
              <div className="flex justify-center md:justify-start gap-4">
                <a 
                  href="https://instagram.com/unisoruyorcom" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-600 hover:text-pink-600 transition-colors group"
                >
                  <div className="w-8 h-8 bg-gradient-to-br from-pink-500 via-red-500 to-yellow-500 rounded-lg flex items-center justify-center text-white group-hover:scale-110 transition-transform">
                    <svg 
                      width="18" 
                      height="18" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      xmlns="http://www.w3.org/2000/svg"
                      className="fill-white"
                    >
                      <path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6m9.65 1.5a1.25 1.25 0 0 1 1.25 1.25A1.25 1.25 0 0 1 17.25 8A1.25 1.25 0 0 1 16 6.75a1.25 1.25 0 0 1 1.25-1.25M12 7a5 5 0 0 1 5 5a5 5 0 0 1-5 5a5 5 0 0 1-5-5a5 5 0 0 1 5-5m0 2a3 3 0 0 0-3 3a3 3 0 0 0 3 3a3 3 0 0 0 3-3a3 3 0 0 0-3-3z"/>
                    </svg>
                  </div>
                </a>
              </div>
            </div>

            {/* Hakkımızda */}
            <div className="text-center md:text-left">
              <h4 className="font-semibold text-gray-900 mb-4">Hakkımızda</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>
                  <a href="/misyonumuz" className="hover:text-orange-600 transition-colors">
                    Misyonumuz
                  </a>
                </li>
                <li>
                  <a href="/topluluk-kurallari" className="hover:text-orange-600 transition-colors">
                    Topluluk Kuralları
                  </a>
                </li>
              </ul>
            </div>

            {/* İletişim */}
            <div className="text-center md:text-left">
              <h4 className="font-semibold text-gray-900 mb-4">İletişim</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>
                  <a 
                    href="mailto:info@unisoruyor.com" 
                    className="hover:text-orange-600 transition-colors flex items-center justify-center md:justify-start gap-2"
                  >
                    <span>✉️</span>
                    info@unisoruyor.com
                  </a>
                </li>
                <li>
                  <a href="/bize-ulasin" className="hover:text-orange-600 transition-colors">
                    Bize Ulaşın
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Footer */}
          <div className="border-t border-gray-200 mt-8 pt-6">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="text-center md:text-left">
                <p className="text-sm text-gray-500 mb-2">
                  © 2025 unisoruyor.com - Tüm hakları saklıdır.
                </p>
                <div className="flex items-center justify-center md:justify-start gap-2 text-sm text-gray-500">
                  <span>Bizi takip edin:</span>
                  <a 
                    href="https://instagram.com/unisoruyorcom" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-pink-500 hover:text-pink-600 transition-colors font-medium"
                  >
                    @unisoruyorcom
                  </a>
                </div>
              </div>
              <div className="flex gap-6 text-sm text-gray-500">
                <a href="/cerez-politikasi" className="hover:text-orange-600 transition-colors">
                  Çerez Politikası
                </a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Public Route Component (allows both logged in and guest users)
const PublicRoute = ({ children }) => {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return children;
};

// Misyonumuz Page
const MisyonumuzPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
      <header className="bg-white shadow-sm border-b border-orange-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.location.href = '/'}>
              <img 
                src="https://customer-assets.emergentagent.com/job_student-forum-1/artifacts/0f9o2m08_ChatGPT%20Image%205%20Eyl%202025%2021_49_28.png" 
                alt="unisoruyor.com logo" 
                className="w-10 h-10 sm:w-12 sm:h-12 object-contain"
              />
              <h1 className="text-lg sm:text-2xl font-bold site-title">unisoruyor.com</h1>
            </div>
            <Button 
              onClick={() => window.location.href = '/'}
              className="bg-orange-500 hover:bg-orange-600 text-white"
            >
              Ana Sayfa
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-gray-900 flex items-center justify-center gap-3">
              <Star className="h-8 w-8 text-orange-500" />
              Misyonumuz
            </CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <div className="space-y-6 text-gray-700 leading-relaxed">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-semibold text-orange-600 mb-4">
                  Türkiye'nin En Büyük Üniversite Topluluğu
                </h2>
                <p className="text-lg text-gray-600">
                  Öğrencilerin akademik ve sosyal gelişimlerine katkıda bulunmak için buradayız
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-orange-50 p-6 rounded-lg">
                  <h3 className="text-xl font-semibold text-orange-700 mb-3 flex items-center gap-2">
                    <BookOpen className="h-5 w-5" />
                    Öğrencilere Yardım
                  </h3>
                  <p>
                    Üniversite hayatında karşılaşılan her türlü sorunla ilgili deneyimli öğrencilerden 
                    yardım alabilir, bilgi paylaşımında bulunabilirsiniz. Akademik sorulardan 
                    sosyal konulara kadar geniş bir yelpazede destek sağlıyoruz.
                  </p>
                </div>

                <div className="bg-blue-50 p-6 rounded-lg">
                  <h3 className="text-xl font-semibold text-blue-700 mb-3 flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Topluluk Eksikliğini Giderme
                  </h3>
                  <p>
                    Üniversite öğrencileri arasında güçlü bir dayanışma ağı oluşturarak, 
                    yalnızlık hissini ortadan kaldırıyor ve öğrencilerin birbirleriyle 
                    bağlantı kurmasını sağlıyoruz.
                  </p>
                </div>

                <div className="bg-green-50 p-6 rounded-lg">
                  <h3 className="text-xl font-semibold text-green-700 mb-3 flex items-center gap-2">
                    <School className="h-5 w-5" />
                    Akademik Başarı
                  </h3>
                  <p>
                    Ders notları paylaşımı, sınav tecrübeleri, proje işbirlikleri ve 
                    akademik rehberlik ile öğrencilerin başarılarını artırmayı hedefliyoruz.
                  </p>
                </div>

                <div className="bg-purple-50 p-6 rounded-lg">
                  <h3 className="text-xl font-semibold text-purple-700 mb-3 flex items-center gap-2">
                    <Heart className="h-5 w-5" />
                    Sosyal Gelişim
                  </h3>
                  <p>
                    Farklı üniversitelerden öğrencilerin buluştuğu bir platform olarak, 
                    sosyal becerilerin gelişmesine ve yeni arkadaşlıkların kurulmasına katkı sağlıyoruz.
                  </p>
                </div>
              </div>

              <div className="text-center bg-gradient-to-r from-orange-100 to-yellow-100 p-6 rounded-lg mt-8">
                <h3 className="text-xl font-semibold text-orange-800 mb-3">
                  Bizimle Birlikte Büyü! 🌟
                </h3>
                <p className="text-gray-700">
                  unisoruyor.com ailesi olarak, her öğrencinin üniversite deneyimini 
                  daha zengin ve anlamlı hale getirmeyi amaçlıyoruz. Sen de bu büyük 
                  topluluğun bir parçası ol!
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

// Topluluk Kuralları Page
const ToplulukKurallariPage = () => {
  const rules = [
    {
      icon: "🤝",
      title: "Saygılı İletişim",
      description: "Tüm kullanıcılara karşı saygılı ve nazik bir dil kullanın. Farklı görüşlere hoşgörü ile yaklaşın."
    },
    {
      icon: "🚫",
      title: "Küfür ve Hakaret Yasak",
      description: "Küfür, hakaret, aşağılayıcı ifadeler ve kişisel saldırılar kesinlikle yasaktır."
    },
    {
      icon: "📵",
      title: "Spam Yasağı",
      description: "Aynı içeriği tekrar tekrar paylaşmak, gereksiz mesajlar göndermek yasaktır."
    },
    {
      icon: "📚",
      title: "Konuyla İlgili Paylaşım",
      description: "Sorularınızı ve cevaplarınızı uygun kategorilerde paylaşın. Off-topic içeriklerden kaçının."
    },
    {
      icon: "🔒",
      title: "Kişisel Bilgi Koruması",
      description: "Kendinizin veya başkalarının kişisel bilgilerini (telefon, adres, TC no vb.) paylaşmayın."
    },
    {
      icon: "📋",
      title: "Telif Hakları",
      description: "Telif hakkı olan içerikleri izinsiz paylaşmayın. Kaynak belirtmeyi unutmayın."
    },
    {
      icon: "🎯",
      title: "Doğru Bilgi Paylaşımı",
      description: "Yanıltıcı, yanlış veya zararlı bilgiler paylaşmayın. Emin olmadığınız konularda kaynak belirtin."
    },
    {
      icon: "🏷️",
      title: "Uygun Etiketleme",
      description: "Sorularınızı uygun başlıklar ve etiketlerle paylaşın. Açıklayıcı başlıklar kullanın."
    },
    {
      icon: "💬",
      title: "Yapıcı Tartışma",
      description: "Tartışmalarda yapıcı olun, fikir alışverişini destekleyin. Kişisel çıkarlar için platform kullanmayın."
    },
    {
      icon: "⚖️",
      title: "Yasal Sınırlar",
      description: "Türkiye Cumhuriyeti yasalarına aykırı içerik paylaşmayın. İllegal aktiviteleri desteklemeyin."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
      <header className="bg-white shadow-sm border-b border-orange-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.location.href = '/'}>
              <img 
                src="https://customer-assets.emergentagent.com/job_student-forum-1/artifacts/0f9o2m08_ChatGPT%20Image%205%20Eyl%202025%2021_49_28.png" 
                alt="unisoruyor.com logo" 
                className="w-10 h-10 sm:w-12 sm:h-12 object-contain"
              />
              <h1 className="text-lg sm:text-2xl font-bold site-title">unisoruyor.com</h1>
            </div>
            <Button 
              onClick={() => window.location.href = '/'}
              className="bg-orange-500 hover:bg-orange-600 text-white"
            >
              Ana Sayfa
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-gray-900 flex items-center justify-center gap-3">
              <Shield className="h-8 w-8 text-orange-500" />
              Topluluk Kuralları
            </CardTitle>
            <CardDescription className="text-lg text-gray-600 mt-4">
              Herkesin güvenli ve rahat edebileceği bir ortam için kurallara uyalım
            </CardDescription>
          </CardHeader>
          <CardContent className="p-8">
            <div className="grid gap-6">
              {rules.map((rule, index) => (
                <div key={index} className="flex gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="text-2xl flex-shrink-0">
                    {rule.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {index + 1}. {rule.title}
                    </h3>
                    <p className="text-gray-700 leading-relaxed">
                      {rule.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 p-6 bg-red-50 border border-red-200 rounded-lg">
              <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Kuralları İhlal Etmenin Sonuçları
              </h3>
              <ul className="space-y-2 text-red-700 text-sm">
                <li>• İlk ihlal: Uyarı mesajı</li>
                <li>• İkinci ihlal: Geçici hesap askıya alma (1-7 gün)</li>
                <li>• Üçüncü ihlal: Kalıcı hesap kapatma</li>
                <li>• Ağır ihlaller: Anında kalıcı yasaklama</li>
              </ul>
            </div>

            <div className="text-center mt-8 p-6 bg-green-50 rounded-lg">
              <p className="text-green-800 font-medium">
                Bu kurallar, topluluk üyelerinin görüşleri alınarak oluşturulmuştur ve 
                herkesin daha iyi bir deneyim yaşaması için sürekli güncellenmektedir.
              </p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

// Çerez Politikası Page
const CerezPolitikasiPage = () => {
  const cookieTypes = [
    {
      title: "Zorunlu Çerezler",
      description: "Sitenin temel işlevlerinin çalışması için gerekli olan çerezlerdir.",
      examples: [
        "Oturum yönetimi (login durumu)",
        "Güvenlik token'ları",
        "Form verilerinin korunması",
        "Dil tercihleri"
      ],
      retention: "Oturum süresi boyunca",
      color: "red"
    },
    {
      title: "Performans Çerezleri",
      description: "Site performansını ölçmek ve kullanıcı deneyimini iyileştirmek için kullanılır.",
      examples: [
        "Sayfa yükleme süreleri",
        "Hata raporları",
        "Site kullanım istatistikleri",
        "En çok ziyaret edilen sayfalar"
      ],
      retention: "2 yıl",
      color: "blue"
    },
    {
      title: "İşlevsellik Çerezleri",
      description: "Kullanıcı tercihlerini hatırlamak ve kişiselleştirilmiş deneyim sunmak için kullanılır.",
      examples: [
        "Tema tercihleri (açık/koyu)",
        "Font boyutu ayarları",
        "Kategori filtreleri",
        "Sayfa başına gösterilecek soru sayısı"
      ],
      retention: "1 yıl",
      color: "green"
    },
    {
      title: "Analitik Çerezler",
      description: "Site trafiğini analiz etmek ve kullanıcı davranışlarını anlamak için kullanılır.",
      examples: [
        "Ziyaretçi sayısı",
        "Trafik kaynakları",
        "En popüler içerik",
        "Kullanıcı etkileşim süreleri"
      ],
      retention: "2 yıl",
      color: "purple"
    }
  ];

  const getColorClasses = (color) => {
    switch(color) {
      case 'red': return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', title: 'text-red-800' };
      case 'blue': return { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', title: 'text-blue-800' };
      case 'green': return { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', title: 'text-green-800' };
      case 'purple': return { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', title: 'text-purple-800' };
      default: return { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700', title: 'text-gray-800' };
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
      <header className="bg-white shadow-sm border-b border-orange-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.location.href = '/'}>
              <img 
                src="https://customer-assets.emergentagent.com/job_student-forum-1/artifacts/0f9o2m08_ChatGPT%20Image%205%20Eyl%202025%2021_49_28.png" 
                alt="unisoruyor.com logo" 
                className="w-10 h-10 sm:w-12 sm:h-12 object-contain"
              />
              <h1 className="text-lg sm:text-2xl font-bold site-title">unisoruyor.com</h1>
            </div>
            <Button 
              onClick={() => window.location.href = '/'}
              className="bg-orange-500 hover:bg-orange-600 text-white"
            >
              Ana Sayfa
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-gray-900 flex items-center justify-center gap-3">
              <Settings className="h-8 w-8 text-orange-500" />
              Çerez Politikası
            </CardTitle>
            <CardDescription className="text-lg text-gray-600 mt-4">
              unisoruyor.com'da kullanılan çerezler hakkında detaylı bilgi
            </CardDescription>
          </CardHeader>
          <CardContent className="p-8">
            {/* Giriş */}
            <div className="mb-8 p-6 bg-orange-50 border border-orange-200 rounded-lg">
              <h2 className="text-xl font-semibold text-orange-800 mb-3">
                Çerezler Nedir?
              </h2>
              <p className="text-gray-700 leading-relaxed">
                Çerezler (cookies), web sitelerinin daha iyi çalışması ve kullanıcı deneyiminin 
                iyileştirilmesi için bilgisayarınızda veya mobil cihazınızda saklanan küçük metin 
                dosyalarıdır. unisoruyor.com olarak, sizlere daha iyi hizmet verebilmek için 
                çeşitli türlerde çerezler kullanmaktayız.
              </p>
            </div>

            {/* Çerez Türleri */}
            <div className="space-y-6 mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Kullandığımız Çerez Türleri
              </h2>
              
              {cookieTypes.map((cookieType, index) => {
                const colors = getColorClasses(cookieType.color);
                return (
                  <div key={index} className={`p-6 ${colors.bg} ${colors.border} border rounded-lg`}>
                    <h3 className={`text-xl font-semibold ${colors.title} mb-3`}>
                      {index + 1}. {cookieType.title}
                    </h3>
                    <p className={`${colors.text} mb-4 leading-relaxed`}>
                      {cookieType.description}
                    </p>
                    
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <h4 className={`font-medium ${colors.title} mb-2`}>Örnekler:</h4>
                        <ul className={`space-y-1 ${colors.text} text-sm`}>
                          {cookieType.examples.map((example, idx) => (
                            <li key={idx}>• {example}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <h4 className={`font-medium ${colors.title} mb-2`}>Saklama Süresi:</h4>
                        <p className={`${colors.text} text-sm`}>
                          {cookieType.retention}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Üçüncü Taraf Çerezler */}
            <div className="mb-8 p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h2 className="text-xl font-semibold text-yellow-800 mb-3">
                Üçüncü Taraf Çerezler
              </h2>
              <p className="text-yellow-700 mb-4 leading-relaxed">
                Bazı durumlarda, güvenilir üçüncü taraf hizmetlerinden çerezler de kullanırız:
              </p>
              <ul className="space-y-2 text-yellow-700 text-sm">
                <li>• <strong>Google Analytics:</strong> Site trafiğini analiz etmek için</li>
                <li>• <strong>CDN Hizmetleri:</strong> Site hızını artırmak için</li>
                <li>• <strong>Güvenlik Hizmetleri:</strong> Spam ve kötüye kullanımı önlemek için</li>
                <li>• <strong>Sosyal Medya:</strong> İçerik paylaşımı için</li>
              </ul>
            </div>

            {/* Çerez Yönetimi */}
            <div className="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
              <h2 className="text-xl font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Çerez Yönetimi
              </h2>
              <div className="space-y-4 text-blue-700">
                <div>
                  <h3 className="font-medium text-blue-800 mb-2">Tarayıcı Ayarları</h3>
                  <p className="text-sm leading-relaxed">
                    Tarayıcınızın ayarlar bölümünden çerezleri yönetebilir, silebilir veya 
                    devre dışı bırakabilirsiniz. Ancak, zorunlu çerezleri devre dışı bırakmanız 
                    durumunda site işlevselliği etkilenebilir.
                  </p>
                </div>
                
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-medium text-blue-800 mb-2">Popüler Tarayıcılar:</h4>
                    <ul className="space-y-1">
                      <li>• Chrome: Ayarlar → Gizlilik → Çerezler</li>
                      <li>• Firefox: Tercihler → Gizlilik → Çerezler</li>
                      <li>• Safari: Tercihler → Gizlilik → Çerezler</li>
                      <li>• Edge: Ayarlar → Gizlilik → Çerezler</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-blue-800 mb-2">Mobil Cihazlar:</h4>
                    <ul className="space-y-1">
                      <li>• iOS Safari: Ayarlar → Safari → Gizlilik</li>
                      <li>• Android Chrome: Chrome → Ayarlar → Site ayarları</li>
                      <li>• Özel mod: Çerezler otomatik silinir</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Yasal Dayanak */}
            <div className="mb-8 p-6 bg-gray-50 border border-gray-200 rounded-lg">
              <h2 className="text-xl font-semibold text-gray-800 mb-3">
                Yasal Dayanak ve Haklarınız
              </h2>
              <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
                <p>
                  <strong>KVKK Uyumu:</strong> Çerez kullanımımız 6698 sayılı Kişisel Verilerin Korunması 
                  Kanunu kapsamında gerçekleştirilmektedir.
                </p>
                <p>
                  <strong>Haklarınız:</strong> Kişisel verilerinizin işlenmesi hakkında bilgi talep etme, 
                  düzeltme, silme ve işleme itiraz etme haklarınız bulunmaktadır.
                </p>
                <p>
                  <strong>İletişim:</strong> Çerez politikası ile ilgili sorularınız için 
                  <a href="mailto:info@unisoruyor.com" className="text-orange-600 hover:text-orange-700 font-medium">
                    {" "}info@unisoruyor.com
                  </a> adresinden bizimle iletişime geçebilirsiniz.
                </p>
              </div>
            </div>

            {/* Güncelleme Bilgisi */}
            <div className="text-center p-4 bg-orange-100 rounded-lg">
              <p className="text-orange-800 font-medium text-sm">
                Bu çerez politikası en son 7 Eylül 2025 tarihinde güncellenmiştir. 
                Değişiklikler bu sayfada yayımlanacaktır.
              </p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

// Bize Ulaşın Page
const BizeUlasınPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
      <header className="bg-white shadow-sm border-b border-orange-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2 cursor-pointer" onClick={() => window.location.href = '/'}>
              <img 
                src="https://customer-assets.emergentagent.com/job_student-forum-1/artifacts/0f9o2m08_ChatGPT%20Image%205%20Eyl%202025%2021_49_28.png" 
                alt="unisoruyor.com logo" 
                className="w-10 h-10 sm:w-12 sm:h-12 object-contain"
              />
              <h1 className="text-lg sm:text-2xl font-bold site-title">unisoruyor.com</h1>
            </div>
            <Button 
              onClick={() => window.location.href = '/'}
              className="bg-orange-500 hover:bg-orange-600 text-white"
            >
              Ana Sayfa
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Card className="shadow-xl border-0 bg-white/95 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-gray-900 flex items-center justify-center gap-3">
              <MessageSquare className="h-8 w-8 text-orange-500" />
              Bize Ulaşın
            </CardTitle>
            <CardDescription className="text-lg text-gray-600 mt-4">
              Sorularınız, önerileriniz veya geri bildirimleriniz için bizimle iletişime geçin
            </CardDescription>
          </CardHeader>
          <CardContent className="p-8">
            <div className="grid md:grid-cols-2 gap-8">
              {/* Email İletişim */}
              <div className="text-center p-6 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors">
                <div className="w-16 h-16 bg-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl text-white">✉️</span>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  E-posta ile İletişim
                </h3>
                <p className="text-gray-600 mb-4">
                  Sorularınız için bize mail gönderin, 24 saat içinde yanıtlıyoruz
                </p>
                <a 
                  href="mailto:info@unisoruyor.com"
                  className="inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  <span>📧</span>
                  info@unisoruyor.com
                </a>
              </div>

              {/* Instagram İletişim */}
              <div className="text-center p-6 bg-pink-50 rounded-lg hover:bg-pink-100 transition-colors">
                <div className="w-16 h-16 bg-gradient-to-br from-pink-500 via-red-500 to-yellow-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg 
                    width="24" 
                    height="24" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    xmlns="http://www.w3.org/2000/svg"
                    className="fill-white"
                  >
                    <path d="M7.8 2h8.4C19.4 2 22 4.6 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8C4.6 22 2 19.4 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2m-.2 2A3.6 3.6 0 0 0 4 7.6v8.8C4 18.39 5.61 20 7.6 20h8.8a3.6 3.6 0 0 0 3.6-3.6V7.6C20 5.61 18.39 4 16.4 4H7.6m9.65 1.5a1.25 1.25 0 0 1 1.25 1.25A1.25 1.25 0 0 1 17.25 8A1.25 1.25 0 0 1 16 6.75a1.25 1.25 0 0 1 1.25-1.25M12 7a5 5 0 0 1 5 5a5 5 0 0 1-5 5a5 5 0 0 1-5-5a5 5 0 0 1 5-5m0 2a3 3 0 0 0-3 3a3 3 0 0 0 3 3a3 3 0 0 0 3-3a3 3 0 0 0-3-3z"/>
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  Instagram
                </h3>
                <p className="text-gray-600 mb-4">
                  Güncel duyurular ve topluluk haberleri için takip edin
                </p>
                <a 
                  href="https://instagram.com/unisoruyorcom"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 bg-gradient-to-r from-pink-500 to-orange-500 hover:from-pink-600 hover:to-orange-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  <span>📱</span>
                  @unisoruyorcom
                </a>
              </div>
            </div>

            {/* İletişim Bilgilendirme */}
            <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Yanıt Süreleri
              </h3>
              <ul className="space-y-2 text-blue-700 text-sm">
                <li>• <strong>E-posta:</strong> 24 saat içinde yanıtlıyoruz</li>
                <li>• <strong>Instagram DM:</strong> Genellikle aynı gün içinde</li>
                <li>• <strong>Acil durumlar:</strong> Öncelikli olarak değerlendirilir</li>
                <li>• <strong>Teknik sorunlar:</strong> En fazla 48 saat içinde çözülür</li>
              </ul>
            </div>

            {/* Hangi Konularda Yazabilirsiniz */}
            <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
                <User className="h-5 w-5" />
                Hangi Konularda Bizimle İletişime Geçebilirsiniz?
              </h3>
              <div className="grid md:grid-cols-2 gap-4 text-green-700 text-sm">
                <ul className="space-y-1">
                  <li>• Teknik sorunlar ve hatalar</li>
                  <li>• Hesap sorunları</li>
                  <li>• Özellik önerileri</li>
                  <li>• Geri bildirimler</li>
                </ul>
                <ul className="space-y-1">
                  <li>• İşbirliği teklifleri</li>
                  <li>• Basın ve medya</li>
                  <li>• Topluluk etkinlikleri</li>
                  <li>• Genel sorular</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

// Main App Component
function App() {
  // Global leaderboard state (shared across all pages)
  const [globalLeaderboard, setGlobalLeaderboard] = useState([]);
  const [leaderboardLoading, setLeaderboardLoading] = useState(false);

  // Fetch leaderboard (can be called from anywhere)
  const fetchGlobalLeaderboard = async () => {
    if (leaderboardLoading) return; // Prevent duplicate requests
    
    setLeaderboardLoading(true);
    try {
      const response = await axios.get(`${API}/leaderboard`);
      setGlobalLeaderboard(response.data.leaderboard || []);
    } catch (err) {
      console.error('Liderlik tablosu yüklenirken hata:', err);
      setGlobalLeaderboard([]);
    } finally {
      setLeaderboardLoading(false);
    }
  };

  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={
              <PublicRoute>
                <Forum 
                  globalLeaderboard={globalLeaderboard}
                  leaderboardLoading={leaderboardLoading}
                  fetchGlobalLeaderboard={fetchGlobalLeaderboard}
                />
              </PublicRoute>
            } />
            <Route path="/misyonumuz" element={<MisyonumuzPage />} />
            <Route path="/topluluk-kurallari" element={<ToplulukKurallariPage />} />
            <Route path="/bize-ulasin" element={<BizeUlasınPage />} />
            <Route path="/cerez-politikasi" element={<CerezPolitikasiPage />} />
          </Routes>
        </div>
      </BrowserRouter>
      <Toaster />
    </AuthProvider>
  );
}

export default App;
