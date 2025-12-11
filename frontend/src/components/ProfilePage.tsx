import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, User, LogOut, Camera, Mail, Phone, MapPin, Briefcase, GraduationCap, Award, FolderKanban, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { UserProfile } from '../App';

interface ProfilePageProps {
  userProfile: UserProfile;
  updateProfile: (profile: UserProfile) => void;
  signOut: () => void;
}

export default function ProfilePage({ userProfile, updateProfile, signOut }: ProfilePageProps) {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState(userProfile);
  const [skillInput, setSkillInput] = useState('');
  const [experienceInput, setExperienceInput] = useState('');
  const [educationInput, setEducationInput] = useState('');
  const [certificationInput, setCertificationInput] = useState('');
  const [projectInput, setProjectInput] = useState('');

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const addSkill = () => {
    if (skillInput.trim() && !formData.skills.includes(skillInput.trim())) {
      setFormData({
        ...formData,
        skills: [...formData.skills, skillInput.trim()],
      });
      setSkillInput('');
    }
  };

  const removeSkill = (skillToRemove: string) => {
    setFormData({
      ...formData,
      skills: formData.skills.filter((skill) => skill !== skillToRemove),
    });
  };

  const addExperience = () => {
    if (experienceInput.trim() && !formData.experience.includes(experienceInput.trim())) {
      setFormData({
        ...formData,
        experience: [...formData.experience, experienceInput.trim()],
      });
      setExperienceInput('');
    }
  };

  const removeExperience = (experienceToRemove: string) => {
    setFormData({
      ...formData,
      experience: formData.experience.filter((experience) => experience !== experienceToRemove),
    });
  };

  const addEducation = () => {
    if (educationInput.trim() && !formData.education?.includes(educationInput.trim())) {
      setFormData({
        ...formData,
        education: [...(formData.education || []), educationInput.trim()],
      });
      setEducationInput('');
    }
  };

  const removeEducation = (educationToRemove: string) => {
    setFormData({
      ...formData,
      education: formData.education?.filter((education) => education !== educationToRemove),
    });
  };

  const addCertification = () => {
    if (certificationInput.trim() && !formData.certificationsAndAchievementsAndAwards?.includes(certificationInput.trim())) {
      setFormData({
        ...formData,
        certificationsAndAchievementsAndAwards: [...(formData.certificationsAndAchievementsAndAwards || []), certificationInput.trim()],
      });
      setCertificationInput('');
    }
  };

  const removeCertification = (certificationToRemove: string) => {
    setFormData({
      ...formData,
      certificationsAndAchievementsAndAwards: formData.certificationsAndAchievementsAndAwards?.filter((certification) => certification !== certificationToRemove),
    });
  };

  const addProject = () => {
    if (projectInput.trim() && !formData.projects?.includes(projectInput.trim())) {
      setFormData({
        ...formData,
        projects: [...(formData.projects || []), projectInput.trim()],
      });
      setProjectInput('');
    }
  };

  const removeProject = (projectToRemove: string) => {
    setFormData({
      ...formData,
      projects: formData.projects?.filter((project) => project !== projectToRemove),
    });
  };

  const handleSave = () => {
    updateProfile(formData);
    setIsEditing(false);
    toast.success('Profile updated successfully!');
  };

  const handleCancel = () => {
    setFormData(userProfile);
    setIsEditing(false);
  };

  const handleSignOut = () => {
    if (window.confirm('Are you sure you want to sign out?')) {
      signOut();
      navigate('/');
      toast.success('Signed out successfully');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/home')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Home</span>
          </button>
          <h2 className="text-gray-900">Profile</h2>
          <div className="w-[100px]" /> {/* Spacer for centering */}
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Profile Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Cover */}
          <div className="h-32 bg-gradient-to-r from-blue-600 to-indigo-600" />

          {/* Profile Info */}
          <div className="px-8 pb-8">
            {/* Profile Photo */}
            <div className="relative -mt-16 mb-6">
              <div className="w-32 h-32 rounded-full border-4 border-white bg-gray-300 flex items-center justify-center overflow-hidden">
                {formData.profilePhoto ? (
                  <img
                    src={formData.profilePhoto}
                    alt="Profile"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-16 h-16 text-gray-600" />
                )}
              </div>
              {isEditing && (
                <button 
                  aria-label="Change profile photo"
                  className="absolute bottom-2 right-2 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white hover:bg-blue-700 transition-colors"
                >
                  <Camera className="w-5 h-5" />
                </button>
              )}
            </div>

            {/* Edit/Save Buttons */}
            <div className="flex justify-end gap-3 mb-6">
              {isEditing ? (
                <>
                  <button
                    onClick={handleCancel}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSave}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Save Changes
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Edit Profile
                </button>
              )}
            </div>

            {/* Form Fields */}
            <div className="space-y-6">
              {/* Name */}
              <div>
                <label htmlFor="name" className="flex items-center gap-2 text-gray-700 mb-2">
                  <User className="w-4 h-4" />
                  Full Name
                </label>
                {isEditing ? (
                  <input
                    id="name"
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  />
                ) : (
                  <p className="text-gray-900">{formData.name}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="flex items-center gap-2 text-gray-700 mb-2">
                  <Mail className="w-4 h-4" />
                  Email
                </label>
                {isEditing ? (
                  <input
                    id="email"
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  />
                ) : (
                  <p className="text-gray-900">{formData.email}</p>
                )}
              </div>

              {/* Phone */}
              <div>
                <label htmlFor="phone" className="flex items-center gap-2 text-gray-700 mb-2">
                  <Phone className="w-4 h-4" />
                  Phone
                </label>
                {isEditing ? (
                  <input
                    id="phone"
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  />
                ) : (
                  <p className="text-gray-900">{formData.phone}</p>
                )}
              </div>

              {/* Location */}
              <div>
                <label htmlFor="location" className="flex items-center gap-2 text-gray-700 mb-2">
                  <MapPin className="w-4 h-4" />
                  Location
                </label>
                {isEditing ? (
                  <input
                    id="location"
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  />
                ) : (
                  <p className="text-gray-900">{formData.location}</p>
                )}
              </div>

              {/* Profile Summary */}
              <div>
                <label htmlFor="profile_summary" className="flex items-center gap-2 text-gray-700 mb-2">
                  <FileText className="w-4 h-4" />
                  Profile Summary
                </label>
                {isEditing ? (
                  <textarea
                    id="profile_summary"
                    name="profile_summary"
                    value={formData.profile_summary}
                    onChange={handleInputChange}
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
                  />
                ) : (
                  <p className="text-gray-900 whitespace-pre-line">{formData.profile_summary}</p>
                )}
              </div>

              {/* Skills */}
              <div>
                <label className="flex items-center gap-2 text-gray-700 mb-2">
                  <Briefcase className="w-4 h-4" />
                  Skills
                </label>
                {isEditing && (
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={skillInput}
                      onChange={(e) => setSkillInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                      placeholder="Add a skill"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    />
                    <button
                      onClick={addSkill}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Add
                    </button>
                  </div>
                )}
                <div className="flex flex-wrap gap-2">
                  {formData.skills.map((skill) => (
                    <span
                      key={skill}
                      className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm flex items-center gap-2"
                    >
                      {skill}
                      {isEditing && (
                        <button
                          onClick={() => removeSkill(skill)}
                          className="hover:text-blue-900"
                        >
                          ×
                        </button>
                      )}
                    </span>
                  ))}
                </div>
              </div>

              {/* Experience */}
              <div>
                <label className="flex items-center gap-2 text-gray-700 mb-2">
                  <Briefcase className="w-4 h-4" />
                  Experience
                </label>
                {isEditing && (
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={experienceInput}
                      onChange={(e) => setExperienceInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addExperience())}
                      placeholder="Add experience"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    />
                    <button
                      onClick={addExperience}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Add
                    </button>
                  </div>
                )}
                <div className="space-y-2">
                  {formData.experience.map((exp, index) => (
                    <div key={index} className="flex items-start justify-between bg-gray-50 p-3 rounded-lg">
                      <p className="text-gray-900 flex-1">{exp}</p>
                      {isEditing && (
                        <button
                          onClick={() => removeExperience(exp)}
                          className="text-gray-500 hover:text-red-600 ml-2"
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Education */}
              {(formData.education && formData.education.length > 0) || isEditing ? (
                <div>
                  <label className="flex items-center gap-2 text-gray-700 mb-2">
                    <GraduationCap className="w-4 h-4" />
                    Education
                  </label>
                  {isEditing && (
                    <div className="flex gap-2 mb-3">
                      <input
                        type="text"
                        value={educationInput}
                        onChange={(e) => setEducationInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addEducation())}
                        placeholder="Add education"
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      />
                      <button
                        onClick={addEducation}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Add
                      </button>
                    </div>
                  )}
                  <div className="space-y-2">
                    {formData.education?.map((edu, index) => (
                      <div key={index} className="flex items-start justify-between bg-gray-50 p-3 rounded-lg">
                        <p className="text-gray-900 flex-1">{edu}</p>
                        {isEditing && (
                          <button
                            onClick={() => removeEducation(edu)}
                            className="text-gray-500 hover:text-red-600 ml-2"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Certifications and Achievements */}
              {(formData.certificationsAndAchievementsAndAwards && formData.certificationsAndAchievementsAndAwards.length > 0) || isEditing ? (
                <div>
                  <label className="flex items-center gap-2 text-gray-700 mb-2">
                    <Award className="w-4 h-4" />
                    Certifications and Achievements and Awards
                  </label>
                  {isEditing && (
                    <div className="flex gap-2 mb-3">
                      <input
                        type="text"
                        value={certificationInput}
                        onChange={(e) => setCertificationInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCertification())}
                        placeholder="Add certification"
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      />
                      <button
                        onClick={addCertification}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Add
                      </button>
                    </div>
                  )}
                  <div className="space-y-2">
                    {formData.certificationsAndAchievementsAndAwards?.map((cert, index) => (
                      <div key={index} className="flex items-start justify-between bg-gray-50 p-3 rounded-lg">
                        <p className="text-gray-900 flex-1">{cert}</p>
                        {isEditing && (
                          <button
                            onClick={() => removeCertification(cert)}
                            className="text-gray-500 hover:text-red-600 ml-2"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Projects */}
              {(formData.projects && formData.projects.length > 0) || isEditing ? (
                <div>
                  <label className="flex items-center gap-2 text-gray-700 mb-2">
                    <FolderKanban className="w-4 h-4" />
                    Projects
                  </label>
                  {isEditing && (
                    <div className="flex gap-2 mb-3">
                      <input
                        type="text"
                        value={projectInput}
                        onChange={(e) => setProjectInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addProject())}
                        placeholder="Add project"
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      />
                      <button
                        onClick={addProject}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        Add
                      </button>
                    </div>
                  )}
                  <div className="space-y-2">
                    {formData.projects?.map((project, index) => (
                      <div key={index} className="flex items-start justify-between bg-gray-50 p-3 rounded-lg">
                        <p className="text-gray-900 flex-1">{project}</p>
                        {isEditing && (
                          <button
                            onClick={() => removeProject(project)}
                            className="text-gray-500 hover:text-red-600 ml-2"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* About */}
              {(formData.about && formData.about.trim()) || isEditing ? (
                <div>
                  <label htmlFor="about" className="flex items-center gap-2 text-gray-700 mb-2">
                    <User className="w-4 h-4" />
                    About
                  </label>
                  {isEditing ? (
                    <textarea
                      id="about"
                      name="about"
                      value={formData.about}
                      onChange={handleInputChange}
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none"
                    />
                  ) : (
                    <p className="text-gray-900 whitespace-pre-line">{formData.about}</p>
                  )}
                </div>
              ) : null}
            </div>

            {/* Sign Out */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={handleSignOut}
                className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                <LogOut className="w-5 h-5" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
