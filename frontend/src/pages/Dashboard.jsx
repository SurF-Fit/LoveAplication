import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, Users, MessageSquare, BarChart3, PlusCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [couple, setCouple] = useState(null);
  const [showCoupleModal, setShowCoupleModal] = useState(false);
  const [coupleCode, setCoupleCode] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Загружаем статистику
      const statsRes = await api.get('/stats');
      setStats(statsRes.data);

      // Загружаем информацию о паре
      const coupleRes = await api.get('/couples/my');
      setCouple(coupleRes.data);
    } catch (error) {
      if (error.response?.status === 404) {
        // Пара не найдена - это нормально для нового пользователя
      }
    }
  };

  const createCouple = async () => {
    try {
      const formData = new FormData();
      formData.append('couple_name', 'Наша пара');

      const response = await api.post('/couples/create', formData);
      toast.success('Пара создана!');
      loadData();
      setShowCoupleModal(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка создания пары');
    }
  };

  const joinCouple = async () => {
    try {
      const formData = new FormData();
      formData.append('couple_code', coupleCode);

      const response = await api.post('/couples/join', formData);
      toast.success('Вы присоединились к паре!');
      loadData();
      setShowCoupleModal(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка присоединения');
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-red-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Привет, {user.username}! 👋
              </h1>
              <p className="text-gray-600 mt-1">
                {couple ? `Вы в паре "${couple.relationship_name}"` : 'Создайте или присоединитесь к паре'}
              </p>
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center space-x-2 px-4 py-2 rounded-full bg-white shadow hover:shadow-md transition-shadow"
              >
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={user.username}
                    className="w-8 h-8 rounded-full"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-pink-500 flex items-center justify-center text-white">
                    {user.username[0].toUpperCase()}
                  </div>
                )}
                <span className="font-medium">{user.username}</span>
              </button>
            </div>
          </div>
        </header>

        {/* Quick Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Совместимость</p>
                  <p className="text-3xl font-bold text-pink-600">{stats.avg_compatibility}%</p>
                </div>
                <Heart className="w-8 h-8 text-pink-400" />
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Пройдено тестов</p>
                  <p className="text-3xl font-bold text-blue-600">{stats.test_count}</p>
                </div>
                <BarChart3 className="w-8 h-8 text-blue-400" />
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Сообщений</p>
                  <p className="text-3xl font-bold text-green-600">{stats.message_count}</p>
                </div>
                <MessageSquare className="w-8 h-8 text-green-400" />
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Партнер</p>
                  <p className="text-xl font-bold text-purple-600">{stats.partner_name}</p>
                </div>
                <Users className="w-8 h-8 text-purple-400" />
              </div>
            </div>
          </div>
        )}

        {/* Main Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <button
            onClick={() => navigate('/tests')}
            className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow text-left group"
          >
            <div className="w-12 h-12 rounded-lg bg-pink-100 flex items-center justify-center mb-4 group-hover:bg-pink-200 transition-colors">
              <BarChart3 className="w-6 h-6 text-pink-600" />
            </div>
            <h3 className="font-bold text-lg mb-2">Пройти тест</h3>
            <p className="text-gray-600 text-sm">
              Узнайте больше о ваших отношениях
            </p>
          </button>

          <button
            onClick={() => navigate('/messages')}
            className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow text-left group"
          >
            <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center mb-4 group-hover:bg-blue-200 transition-colors">
              <MessageSquare className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-bold text-lg mb-2">Сообщения</h3>
            <p className="text-gray-600 text-sm">
              Оставьте сообщение партнеру
            </p>
          </button>

          <button
            onClick={() => navigate('/couple')}
            className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow text-left group"
          >
            <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center mb-4 group-hover:bg-green-200 transition-colors">
              <Users className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="font-bold text-lg mb-2">Наша пара</h3>
            <p className="text-gray-600 text-sm">
              Информация о ваших отношениях
            </p>
          </button>

          <button
            onClick={() => setShowCoupleModal(true)}
            className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-shadow text-left group"
          >
            <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center mb-4 group-hover:bg-purple-200 transition-colors">
              <PlusCircle className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-bold text-lg mb-2">
              {couple ? 'Изменить' : 'Создать пару'}
            </h3>
            <p className="text-gray-600 text-sm">
              {couple ? 'Обновить информацию' : 'Пригласите партнера'}
            </p>
          </button>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl p-6 shadow-lg">
          <h2 className="text-xl font-bold mb-4">Последняя активность</h2>
          <div className="space-y-4">
            {couple && couple.partners?.map(partner => (
              <div key={partner.id} className="flex items-center p-4 bg-gray-50 rounded-lg">
                <div className="w-10 h-10 rounded-full bg-pink-500 flex items-center justify-center text-white mr-4">
                  {partner.avatar_url ? (
                    <img src={partner.avatar_url} alt="" className="w-full h-full rounded-full" />
                  ) : (
                    partner.username[0].toUpperCase()
                  )}
                </div>
                <div>
                  <p className="font-medium">{partner.username}</p>
                  <p className="text-sm text-gray-500">
                    {partner.gender === 'male' ? 'Мужчина' : 'Девушка'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Couple Modal */}
        {showCoupleModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl p-6 max-w-md w-full">
              <h3 className="text-xl font-bold mb-4">
                {couple ? 'Обновить пару' : 'Создать или присоединиться'}
              </h3>

              {!couple ? (
                <div className="space-y-4">
                  <button
                    onClick={createCouple}
                    className="w-full bg-pink-500 text-white py-3 rounded-lg font-medium hover:bg-pink-600 transition-colors"
                  >
                    Создать новую пару
                  </button>

                  <div className="text-center text-gray-500">или</div>

                  <div>
                    <input
                      type="text"
                      placeholder="Введите код пары"
                      value={coupleCode}
                      onChange={(e) => setCoupleCode(e.target.value)}
                      className="w-full border rounded-lg px-4 py-3 mb-3"
                    />
                    <button
                      onClick={joinCouple}
                      className="w-full bg-blue-500 text-white py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors"
                    >
                      Присоединиться к паре
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <p className="mb-4">Код вашей пары: <strong>{couple.couple_code}</strong></p>
                  <p className="text-sm text-gray-500 mb-4">
                    Поделитесь этим кодом с партнером для присоединения
                  </p>
                </div>
              )}

              <button
                onClick={() => setShowCoupleModal(false)}
                className="w-full border border-gray-300 py-3 rounded-lg font-medium mt-4 hover:bg-gray-50 transition-colors"
              >
                Закрыть
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;