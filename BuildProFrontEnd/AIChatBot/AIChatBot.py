from flask import Flask, request, jsonify
from openai import OpenAI
import json
import re

app = Flask(__name__)

# OpenAI client initialization
openai_api_key = "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"  # Use your OpenAI API key here
client = OpenAI(api_key=openai_api_key)

# Store messages in-memory per user
user_memory = {}

def generate_project_timeline(project_description):
    """Generate construction project timeline using OpenAI"""
    
    system_prompt = """
You are an expert construction project manager with 20+ years of experience in Sri Lankan construction industry.
Your task is to create detailed, realistic construction timelines based on project descriptions with Sri Lankan context.

Consider Sri Lankan factors:
- Monsoon season delays (May-September and October-January)
- Local building regulations and permit processes
- Sri Lankan material costs and availability
- Local labor rates and working conditions
- Currency in Sri Lankan Rupees (LKR)

IMPORTANT: Respond ONLY with valid JSON in this exact format:
{
    "project_summary": "Brief description of the project",
    "total_estimated_duration": "X weeks/months",
    "phases": [
        {
            "phase_name": "Phase Name",
            "tasks": [
                {
                    "task_name": "Task Name",
                    "duration": "X days/weeks",
                    "dependencies": ["Previous Task Name"] or [],
                    "description": "Brief description of what this task involves",
                    "critical_path": true/false,
                    "estimated_cost": "LKR X,XXX,XXX"
                }
            ]
        }
    ],
    "critical_considerations": [
        "Important factor 1 (Sri Lankan context)",
        "Important factor 2 (weather/monsoon)",
        "Important factor 3 (permits/regulations)"
    ],
    "estimated_budget_range": "LKR X,XXX,XXX - LKR X,XXX,XXX",
    "seasonal_recommendations": "Best time to start project considering Sri Lankan weather"
}

Rules:
- Be realistic with Sri Lankan timeframes
- Consider monsoon weather dependencies
- Include Sri Lankan permit and inspection time
- Account for local material delivery delays
- Mark critical path items
- Provide practical Sri Lankan construction advice
- All costs in Sri Lankan Rupees (LKR)
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a construction timeline for Sri Lankan context: {project_description}"}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = completion.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            return get_fallback_response(project_description)
            
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return get_fallback_response(project_description)

def get_fallback_response(project_description):
    """Fallback response when API fails - Sri Lankan context"""
    return {
        "project_summary": f"Sri Lankan construction project: {project_description}",
        "total_estimated_duration": "14-18 weeks",
        "phases": [
            {
                "phase_name": "Planning & Permits",
                "tasks": [
                    {
                        "task_name": "Obtain building permits from local council",
                        "duration": "3-6 weeks",
                        "dependencies": [],
                        "description": "Submit plans to Urban Development Authority and local council",
                        "critical_path": True,
                        "estimated_cost": "LKR 150,000 - 300,000"
                    }
                ]
            },
            {
                "phase_name": "Foundation Work",
                "tasks": [
                    {
                        "task_name": "Site excavation and foundation",
                        "duration": "2-3 weeks",
                        "dependencies": ["Obtain building permits from local council"],
                        "description": "Excavation and concrete foundation work",
                        "critical_path": True,
                        "estimated_cost": "LKR 800,000 - 1,200,000"
                    }
                ]
            }
        ],
        "critical_considerations": [
            "Avoid starting during monsoon seasons (May-Sep, Oct-Jan)",
            "Sri Lankan building permits can take 3-6 weeks",
            "Material costs fluctuate with import restrictions"
        ],
        "estimated_budget_range": "LKR 3,500,000 - LKR 6,000,000",
        "seasonal_recommendations": "Best to start February-April or September-October to avoid heavy rains"
    }

@app.route('/chat/<user_id>', methods=['POST'])
def chat(user_id):
    data = request.json
    message = data.get('message')

    try:
        # Initialize memory if not already
        if user_id not in user_memory:
            user_memory[user_id] = [{
                "role": "system",
                "content": (
                    "You are a Sri Lankan construction project management expert 🏗️. "
                    "Help users plan construction projects with detailed timelines and Sri Lankan Rupee (LKR) cost estimates. "
                    "Consider Sri Lankan building regulations, monsoon seasons, local material costs, and ICTAD/CIDA standards. "
                    "When user asks for project timeline, provide structured response with phases, tasks, durations, and LKR costs. "
                    "Use clear examples and emojis to improve readability 📚."
                )
            }]

        # Check if user is asking for project timeline generation
        timeline_keywords = ['timeline', 'project plan', 'construction plan', 'build', 'house', 'building', 'construct']
        is_project_request = any(keyword in message.lower() for keyword in timeline_keywords)
        
        if is_project_request and len(message) > 20:
            # Generate structured project timeline
            timeline_data = generate_project_timeline(message)
            
            # Format timeline as readable response
            formatted_response = f"""
🏗️ **PROJECT TIMELINE GENERATED** 🏗️

**Project:** {timeline_data['project_summary']}
**Total Duration:** {timeline_data['total_estimated_duration']}
**Budget Range:** {timeline_data['estimated_budget_range']}

📋 **CONSTRUCTION PHASES:**

"""
            
            for i, phase in enumerate(timeline_data['phases'], 1):
                formatted_response += f"**{i}. {phase['phase_name']}**\n"
                for task in phase['tasks']:
                    critical_badge = "🔴 CRITICAL" if task['critical_path'] else "🟢"
                    formatted_response += f"   • {task['task_name']} - {task['duration']}\n"
                    formatted_response += f"     Cost: {task['estimated_cost']} {critical_badge}\n"
                    formatted_response += f"     {task['description']}\n"
                    if task['dependencies']:
                        formatted_response += f"     Dependencies: {', '.join(task['dependencies'])}\n"
                    formatted_response += "\n"
            
            formatted_response += "⚠️ **CRITICAL CONSIDERATIONS:**\n"
            for consideration in timeline_data['critical_considerations']:
                formatted_response += f"• {consideration}\n"
            
            formatted_response += f"\n🌦️ **SEASONAL ADVICE:** {timeline_data['seasonal_recommendations']}"
            
            # Store the structured response
            user_memory[user_id].append({"role": "user", "content": message})
            user_memory[user_id].append({"role": "assistant", "content": formatted_response})
            
            ai_response = (
                "<div style='font-family: Arial, sans-serif; color: #333;'>"
                f"{formatted_response.replace('\n', '<br>')}"
                "</div>"
            )
            
        else:
            # Regular chat about construction/projects
            user_memory[user_id].append({"role": "user", "content": message})

            # Chat completion
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=user_memory[user_id]
            )

            # Extract and store response
            raw_response = completion.choices[0].message.content.strip()
            user_memory[user_id].append({"role": "assistant", "content": raw_response})

            ai_response = (
                "<div style='font-family: Arial, sans-serif; color: #333;'>"
                f"{raw_response.replace('\n', '<br>')}"
                "</div>"
            )

    except Exception as e:
        ai_response = f"<div style='color:red;'>Error generating response: {e}</div>"

    return jsonify({
        "userId": user_id,
        "message": ai_response,
        "sender": "ai"
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=True)