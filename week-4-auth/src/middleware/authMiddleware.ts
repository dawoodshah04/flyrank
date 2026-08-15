import supabase from '@supabase/supabase-js'

export async function authMiddleware(req, res, next):Promise<void>{
    const authHeader = req.header.authorization;

    if(!authHeader || !authHeader.startsWith('Bearer')){
        return res.status(401).json({"message":"Access Token required"})
    }

    const token = authHeader.split(" ")[1];

    if(!token){
        return res.status(401).json({error:"Access Token required"})
    }

    const { data, error } = await supabase.auth.getUser(token);
    
    if(error || !data.user){
        return res.status(401).json({ error: "Invalid or expired token" });
    }
    req.user = data.user;
    next();
}

