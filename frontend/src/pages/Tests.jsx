import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Clock, Heart, TrendingUp } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

const Tests = () => {
  const navigate = useNavigate();
  const [availableTests, setAvailableTests] = useState([]);
  const [results, setResults] = useState({ personal: [], shared: [] });
  const [selectedTest, setSelectedTest] = useState(null);
  const [answers, setAnswers] = useState([]);

  useEffect(() => {
    loadTests();
    loadResults();
  }, []);

  const loadTests = async () => {
    try {
      const response = await api.get('/tests/available');
      setAvailableTests(response.data);
    } catch (error) {
      toast.error('Ошибка загрузки тестов');
    }
  };

  const loadResults = async () => {
    try {
      const response = await api.get('/tests/results');
      setResults(response.data);
    } catch (error) {
      console.error('Error loading results:', error);
    }
  };

  const startTest = async (testTitle) => {
  const formData = new FormData();
  formData.append('test_title', testTitle);

  const response = await api.post('/tests/start', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

  const handleAnswer = (questionId, value) => {
    setAnswers(prev => {
      const filtered = prev.filter(a => a.question_id !== questionId);
      return [...filtered, { question_id: questionId, answer_value: value }];
    });
  };

  const submitTest = async () => {
    try {
      await api.post(`/tests/${selectedTest.test_id}/submit`, answers);
      toast.success('Результаты сохранены!');
      setSelectedTest(null);
      setAnswers([]);
      loadResults();
    } catch (error) {
      toast.error('Ошибка сохранения результатов');
    }
  };

  if (selectedTest) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-red-50 p-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <button
              onClick={() => setSelectedTest(null)}
              className="text-pink-600 hover:text-pink-700 mb-6"
            >
              ← Назад к тестам
            </button>

            <h1 className="text-2xl font-bold mb-2">{selectedTest.title}</h1>
            <p className="text-gray-600 mb-8">{selectedTest.description}</p>

            <div className="space-y-8">
              {selectedTest.questions.map((question) => (
                <div key={question.id} className="border-b pb-6">
                  <h3 className="text-lg font-medium mb-4">
                    {question.id}. {question.text}
                  </h3>
                  <div className="space-y-2">
                    {question.options.map((option, index) => (
                      <button
                        key={index}
                        onClick={() => handleAnswer(question.id, option.value)}
                        className={`w-full text-left p-4 rounded-lg border transition-colors ${
                          answers.find(a => a.question_id === question.id && a.answer_value === option.value)
                            ? 'border-pink-500 bg-pink-50'
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        {option.text}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={submitTest}
              disabled={answers.length < selectedTest.questions.length}
              className={`w-full mt-8 py-3 rounded-lg font-medium transition-colors ${
                answers.length < selectedTest.questions.length
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-pink-500 text-white hover:bg-pink-600'
              }`}
            >
              Завершить тест
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-red-50 p-4">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Тесты отношений</h1>
          <p className="text-gray-600 mt-1">Пройдите тесты вместе с партнером</p>
        </header>

        {/* Available Tests */}
        <div className="mb-12">
          <h2 className="text-xl font-bold mb-6">Доступные тесты</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {availableTests.map((test) => (
              <div key={test.title} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow">
                <div className="p-6">
                  <div className="flex items-center mb-4">
                    <div className="w-10 h-10 rounded-lg bg-pink-100 flex items-center justify-center mr-3">
                      <Heart className="w-5 h-5 text-pink-600" />
                    </div>
                    <div>
                      <h3 className="font-bold">{test.title}</h3>
                      <p className="text-sm text-gray-500">{test.category}</p>
                    </div>
                  </div>
                  <p className="text-gray-600 text-sm mb-6">{test.description}</p>
                  <button
                    onClick={() => startTest(test)}
                    className="w-full bg-pink-500 text-white py-3 rounded-lg font-medium hover:bg-pink-600 transition-colors flex items-center justify-center"
                  >
                    Начать тест <ChevronRight className="w-4 h-4 ml-2" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Results */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Personal Results */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold mb-6">Мои результаты</h2>
            <div className="space-y-4">
              {results.personal.length > 0 ? (
                results.personal.map((result, index) => (
                  <div key={index} className="border-l-4 border-pink-500 pl-4 py-2">
                    <div className="flex justify-between items-center">
                      <h3 className="font-medium">{result.test_title}</h3>
                      <span className="text-pink-600 font-bold">{result.score}/10</span>
                    </div>
                    <p className="text-gray-600 text-sm mt-1">{result.interpretation}</p>
                    <p className="text-gray-400 text-xs mt-2">
                      {new Date(result.completed_at).toLocaleDateString()}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">
                  Вы еще не проходили тесты
                </p>
              )}
            </div>
          </div>

          {/* Shared Results */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold mb-6">Результаты пары</h2>
            <div className="space-y-4">
              {results.shared.length > 0 ? (
                results.shared.map((result, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="flex justify-between items-center">
                      <h3 className="font-medium">{result.test_title}</h3>
                      <div className="flex items-center">
                        <TrendingUp className="w-4 h-4 text-blue-500 mr-2" />
                        <span className="text-blue-600 font-bold">
                          {result.compatibility_percentage}%
                        </span>
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm mt-1">
                      Общий балл: {result.combined_score}/10
                    </p>
                    <p className="text-gray-400 text-xs mt-2">
                      {new Date(result.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">
                  Нет общих результатов
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Tests;